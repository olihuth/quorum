"""Quorum IoT Civic Voting Totem Gateway & Hardware Telemetry Simulator.

Mirrors the Arduino Uno R3 TinkerCad circuit (`quorum_voting_totem.ino`):
- Ultrasonic PING))) proximity sensor on Pin 13 (presence gate <= 100 cm)
- Ambient LDR photoresistor on Pin A0 driving LCD PWM backlight on Pin 3
- Debounced physical pushbuttons on Pin 7 (upvote / favor) and Pin 8 (downvote / against)
- 16x2 HD44780 LCD telemetry display
- HTTP bridge posting votes directly to FastAPI `POST /api/v1/iot/vote`
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_API_URL = "http://localhost:8000/api/v1"
DEFAULT_TOTEM_ID = "totem-metro-se-01"
PRESENCE_THRESHOLD_CM = 100
HTTP_TIMEOUT_SECONDS = 2.5


@dataclass
class TargetBillContext:
    """Resolved proposition context shown on the totem LCD and sent to the API."""

    bill_id: int
    number: str
    title: str
    votes_favor: int
    votes_against: int
    api_online: bool


def compute_adaptive_backlight(light_level: int, citizen_present: bool) -> int:
    """Replicate Arduino map(lightLevel, 0, 1023, 80, 255) with standby dimming."""
    if not citizen_present:
        return 30
    clamped = max(0, min(1023, int(light_level)))
    return max(80, min(255, round(80 + (clamped / 1023.0) * (255 - 80))))


def render_lcd_frame(line1: str, line2: str, backlight_pwm: int) -> str:
    """Render an authentic 16x2 character LCD display block."""
    row1 = f"{line1[:16]:<16}"
    row2 = f"{line2[:16]:<16}"
    return (
        f"  LCD 16x2 (PWM Backlight Pin 3: {backlight_pwm}/255)\n"
        f"  +------------------+\n"
        f"  | {row1} |\n"
        f"  | {row2} |\n"
        f"  +------------------+"
    )


def resolve_target_bill(api_url: str, explicit_bill_id: int | None) -> TargetBillContext:
    """Fetch target bill metadata from FastAPI or fall back offline cleanly."""
    url = f"{api_url.rstrip('/')}/bills"
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "Quorum-IoT-Gateway/1.0"},
        )
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            bills = json.loads(response.read().decode("utf-8"))
        if isinstance(bills, list) and bills:
            selected = None
            if explicit_bill_id is not None:
                selected = next((b for b in bills if int(b.get("id", -1)) == explicit_bill_id), None)
            if selected is None:
                selected = bills[0]
            return TargetBillContext(
                bill_id=int(selected["id"]),
                number=str(selected.get("number", f"PL #{selected['id']}")),
                title=str(selected.get("title", "Proposição Legislativa")),
                votes_favor=int(selected.get("votes_favor", 0)),
                votes_against=int(selected.get("votes_against", 0)),
                api_online=True,
            )
    except Exception:
        pass

    return TargetBillContext(
        bill_id=explicit_bill_id or 1,
        number="PL 2338/2023",
        title="Marco Legal da Inteligência Artificial no Brasil",
        votes_favor=1840,
        votes_against=360,
        api_online=False,
    )


def post_iot_vote(
    api_url: str,
    totem_id: str,
    bill_ctx: TargetBillContext,
    choice: str,
    session_token: str | None = None,
) -> dict[str, Any]:
    """Post an IoT totem vote to FastAPI POST /api/v1/iot/vote with offline fallback."""
    endpoint = f"{api_url.rstrip('/')}/iot/vote"
    token = session_token or f"totem-sess-{uuid4().hex[:12]}"
    payload = {
        "totem_id": totem_id,
        "bill_id": bill_ctx.bill_id,
        "choice": choice,
        "session_token": token,
    }

    try:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Quorum-IoT-Gateway/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            bill_ctx.votes_favor = int(data.get("votes_favor", bill_ctx.votes_favor))
            bill_ctx.votes_against = int(data.get("votes_against", bill_ctx.votes_against))
            return {
                "mode": "API FastAPI ao vivo (HTTP 200)",
                "endpoint": endpoint,
                "source": data.get("source", "iot_totem"),
                "votes_favor": bill_ctx.votes_favor,
                "votes_against": bill_ctx.votes_against,
                "favor_percentage": float(data.get("favor_percentage", 0.0)),
                "message": str(data.get("message", "Voto registrado com sucesso.")),
            }
    except Exception as exc:
        if choice == "favor":
            bill_ctx.votes_favor += 1
        else:
            bill_ctx.votes_against += 1
        total = bill_ctx.votes_favor + bill_ctx.votes_against
        favor_pct = round((bill_ctx.votes_favor / total) * 100.0, 1) if total > 0 else 0.0
        return {
            "mode": f"Simulação Local Offline (Backend indisponível: {type(exc).__name__})",
            "endpoint": endpoint,
            "source": "iot_totem",
            "votes_favor": bill_ctx.votes_favor,
            "votes_against": bill_ctx.votes_against,
            "favor_percentage": favor_pct,
            "message": "Telemetria validada localmente pronta para sincronização HTTP POST.",
        }


def process_telemetry_step(
    *,
    step_label: str,
    api_url: str,
    totem_id: str,
    bill_ctx: TargetBillContext,
    distance_cm: int,
    light_level: int,
    button_choice: str | None,
    counters: dict[str, int],
) -> None:
    """Evaluate sensor readings, enforce PING presence gate, render LCD, and dispatch vote."""
    citizen_present = 0 < distance_cm <= PRESENCE_THRESHOLD_CM
    pwm = compute_adaptive_backlight(light_level, citizen_present)
    presence_status = "CIDADÃO DETECTADO (Ativo)" if citizen_present else "AGUARDANDO (Standby)"

    print(f"\n[{step_label}]")
    print(
        f"  Sensores : PING))) Pin 13 = {distance_cm} cm [{presence_status}] | "
        f"LDR Pin A0 = {light_level}/1023 -> Backlight PWM = {pwm}/255"
    )

    if not citizen_present:
        if button_choice is not None:
            print(
                f"  Botão    : Pressionado ({button_choice}) -> BLOQUEADO "
                f"(sensor ultrassônico > {PRESENCE_THRESHOLD_CM} cm evita votos acidentais)"
            )
            counters["blocked"] += 1
        print(render_lcd_frame("     Quorum     ", "Aproxime p/votar", pwm))
        return

    print(render_lcd_frame(bill_ctx.number, f"Sim:{counters['favor']} Nao:{counters['against']}", pwm))

    if button_choice is None:
        return

    pin_label = "upvotePin (Pin 7)" if button_choice == "favor" else "downvotePin (Pin 8)"
    pt_choice = "A Favor" if button_choice == "favor" else "Contra"
    counters[button_choice] += 1
    counters["sent"] += 1

    print(f"  Entrada  : Botão físico {pin_label} -> Voto '{pt_choice}' ({button_choice})")
    serial_frame = {
        "event": "vote",
        "totem_id": totem_id,
        "bill_id": bill_ctx.bill_id,
        "choice": button_choice,
        "distance_cm": distance_cm,
        "light_level": light_level,
        "backlight_pwm": pwm,
        "upvotes": counters["favor"],
        "downvotes": counters["against"],
    }
    print(f"  Serial   : {json.dumps(serial_frame, ensure_ascii=False)}")

    api_result = post_iot_vote(api_url, totem_id, bill_ctx, button_choice)
    print(
        f"  Gateway  : POST {api_result['endpoint']} -> {api_result['mode']} | "
        f"Placar {bill_ctx.number}: {api_result['votes_favor']} A Favor / "
        f"{api_result['votes_against']} Contra ({api_result['favor_percentage']}%)"
    )
    print(render_lcd_frame("Voto registrado!", "Obrigado cidadao", pwm))


def run_demo_sequence(api_url: str, totem_id: str, bill_ctx: TargetBillContext) -> None:
    """Execute automated showcase sequence covering standby, light adaptation, and 3 votes."""
    counters = {"favor": 0, "against": 0, "sent": 0, "blocked": 0}
    scenarios: list[tuple[str, int, int, str | None]] = [
        ("Evento 1 — Modo Standby & Trava Anti-Acidente", 185, 220, "favor"),
        ("Evento 2 — Dia Claro + Voto 'A Favor' (Pin 7)", 42, 860, "favor"),
        ("Evento 3 — Estação Noturna + Voto 'Contra' (Pin 8)", 58, 290, "against"),
        ("Evento 4 — Iluminação Moderada + Voto 'A Favor' (Pin 7)", 36, 610, "favor"),
    ]

    for label, dist_cm, ldr_val, choice in scenarios:
        process_telemetry_step(
            step_label=label,
            api_url=api_url,
            totem_id=totem_id,
            bill_ctx=bill_ctx,
            distance_cm=dist_cm,
            light_level=ldr_val,
            button_choice=choice,
            counters=counters,
        )

    print("\n" + "-" * 78)
    print(
        f"RESUMO TELEMETRIA IoT ({totem_id} | {bill_ctx.number}): "
        f"{counters['sent']} votos enviados (source=iot_totem: "
        f"{counters['favor']} A Favor, {counters['against']} Contra) | "
        f"{counters['blocked']} tentativa fora de alcance bloqueada"
    )
    print("=" * 78)


def run_interactive_kiosk(api_url: str, totem_id: str, bill_ctx: TargetBillContext) -> None:
    """Run interactive CLI kiosk simulator useful for live MVP pitch recordings."""
    counters = {"favor": 0, "against": 0, "sent": 0, "blocked": 0}
    distance_cm = 45
    light_level = 650

    print("\nModo Totem Interativo ativado.")
    print("Comandos: [1] Votar A Favor (Pin 7) | [2] Votar Contra (Pin 8) | [d N] Distância cm | [l N] Luz LDR 0-1023 | [q] Sair")

    while True:
        pwm = compute_adaptive_backlight(light_level, 0 < distance_cm <= PRESENCE_THRESHOLD_CM)
        print(f"\nEstado atual -> PING: {distance_cm} cm | LDR: {light_level} | PWM: {pwm}/255 | {bill_ctx.number}")
        try:
            cmd = input("Totem > ").strip().lower()
        except EOFError:
            break

        if cmd in ("q", "sair", "exit"):
            break
        if cmd == "1":
            process_telemetry_step(
                step_label="Interação Manual — Botão Pin 7",
                api_url=api_url,
                totem_id=totem_id,
                bill_ctx=bill_ctx,
                distance_cm=distance_cm,
                light_level=light_level,
                button_choice="favor",
                counters=counters,
            )
        elif cmd == "2":
            process_telemetry_step(
                step_label="Interação Manual — Botão Pin 8",
                api_url=api_url,
                totem_id=totem_id,
                bill_ctx=bill_ctx,
                distance_cm=distance_cm,
                light_level=light_level,
                button_choice="against",
                counters=counters,
            )
        elif cmd.startswith("d "):
            try:
                distance_cm = max(0, int(cmd.split()[1]))
                print(f"Distância PING))) ajustada para {distance_cm} cm.")
            except ValueError:
                print("Uso inválido. Exemplo: d 40 (ou d 180 para testar standby).")
        elif cmd.startswith("l "):
            try:
                light_level = max(0, min(1023, int(cmd.split()[1])))
                print(f"Luminosidade LDR ajustada para {light_level}/1023.")
            except ValueError:
                print("Uso inválido. Exemplo: l 900.")
        else:
            print("Comando não reconhecido. Use 1, 2, d <cm>, l <0-1023> ou q.")


def run_serial_bridge(port: str, baud: int, api_url: str, totem_id: str, bill_ctx: TargetBillContext) -> None:
    """Bridge live JSON lines from an Arduino Uno USB Serial port to FastAPI."""
    try:
        import serial  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Para ler uma porta Serial física (--serial), instale pyserial: pip install pyserial"
        ) from exc

    counters = {"favor": 0, "against": 0, "sent": 0, "blocked": 0}
    print(f"\nEscutando Arduino Uno na porta {port} ({baud} baud)... Pressione Ctrl+C para sair.")
    with serial.Serial(port, baud, timeout=1) as ser:
        while True:
            raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw_line:
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                print(f"[Serial Raw] {raw_line}")
                continue

            if event.get("event") == "vote":
                process_telemetry_step(
                    step_label="Arduino Serial Ao Vivo",
                    api_url=api_url,
                    totem_id=str(event.get("totem_id") or totem_id),
                    bill_ctx=bill_ctx,
                    distance_cm=int(event.get("distance_cm", 50)),
                    light_level=int(event.get("light_level", 600)),
                    button_choice="favor" if event.get("choice") == "favor" else "against",
                    counters=counters,
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quorum IoT Voting Totem Gateway")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="FastAPI base URL (default: http://localhost:8000/api/v1)")
    parser.add_argument("--totem-id", default=DEFAULT_TOTEM_ID, help="Physical totem hardware identifier")
    parser.add_argument("--bill-id", type=int, default=None, help="Target legislative bill ID")
    parser.add_argument("--interactive", action="store_true", help="Interactive kiosk simulator mode")
    parser.add_argument("--serial", default=None, help="Read live JSON frames from USB Serial port (e.g. COM3)")
    parser.add_argument("--baud", type=int, default=9600, help="Serial baud rate (default: 9600)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bill_ctx = resolve_target_bill(args.api_url, args.bill_id)

    print("=" * 78)
    print("QUORUM IoT — GATEWAY DE TELEMETRIA E VOTAÇÃO CIDADÃ PRESENCIAL")
    print("=" * 78)
    print(f"Hardware  : Arduino Uno R3 + Sensor PING))) (Pin 13) + LDR (A0) + LCD 16x2")
    print(f"Totem ID  : {args.totem_id}")
    print(f"Proposição: [{bill_ctx.bill_id}] {bill_ctx.number} — {bill_ctx.title}")
    print(f"Backend   : {'Online em ' + args.api_url if bill_ctx.api_online else 'Offline (modo demonstração local)'}")

    if args.serial:
        run_serial_bridge(args.serial, args.baud, args.api_url, args.totem_id, bill_ctx)
    elif args.interactive:
        run_interactive_kiosk(args.api_url, args.totem_id, bill_ctx)
    else:
        run_demo_sequence(args.api_url, args.totem_id, bill_ctx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
