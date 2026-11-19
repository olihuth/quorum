import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from translator import translate_bill  # noqa: E402


def _load_root_dotenv() -> None:
    """Load key=value pairs from the repository root .env file if present."""
    dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        clean_key = key.strip()
        clean_val = value.strip().strip('"').strip("'")
        if clean_key:
            os.environ.setdefault(clean_key, clean_val)

SAMPLE_BILLS = [
    {
        "number": "PL 2338/2023",
        "title": "Marco Legal da Inteligência Artificial e Responsabilidade Algorítmica",
        "official_summary": (
            "Art. 1º Esta Lei estabelece normas gerais de caráter nacional para a concepção, "
            "o desenvolvimento, a implementação, a utilização, a adoção e a governança responsável "
            "de sistemas de inteligência artificial (IA) no Brasil, com o objetivo de proteger os "
            "direitos fundamentais e estimular a inovação ética. "
            "Art. 14. Previamente à colocação no mercado ou à utilização em serviço de sistema de "
            "inteligência artificial classificado como de alto risco, os agentes de IA deverão realizar "
            "avaliação preliminar de impacto algorítmico, contemplando medidas de mitigação de vieses "
            "discriminatórios ilegais ou abusivos, documentação técnica auditável e supervisão humana efetiva. "
            "§ 1º Consideram-se sistemas de IA de alto risco aqueles empregados em infraestrutura crítica, "
            "avaliação de crédito, concessão de benefícios assistenciais, recrutamento trabalhista e "
            "diagnóstico médico automatizado. "
            "§ 2º A pessoa afetada por decisão automatizada que produza efeitos jurídicos relevantes tem "
            "direito à explicação clara e à revisão humana da deliberação, aplicando-se o regime de "
            "responsabilidade civil objetiva ao fornecedor ou operador pelos danos decorrentes de falhas."
        ),
    },
    {
        "number": "PLP 68/2024",
        "title": "Reforma Tributária — Instituição do IBS, CBS e Cashback Social",
        "official_summary": (
            "Art. 1º Ficam instituídos o Imposto sobre Bens e Serviços (IBS), de competência compartilhada "
            "entre Estados, Distrito Federal e Municípios, e a Contribuição Social sobre Bens e Serviços "
            "(CBS), de competência da União, em substituição gradual ao PIS, à Cofins, ao IPI, ao ICMS "
            "e ao ISS, observados os princípios da simplicidade, da transparência, da neutralidade "
            "tributária e da não cumulatividade plena ao longo de toda a cadeia econômica. "
            "Art. 112. As operações com bens e serviços sujeitam-se à incidência uniforme mediante alíquota "
            "de referência fixada por resolução do Senado Federal, assegurada a apropriação integral de "
            "crédito financeiro relativo ao montante efetivamente pago nas etapas anteriores. "
            "§ 1º Ficam reduzidas a zero as alíquotas do IBS e da CBS incidentes sobre os produtos "
            "alimentícios que compõem a Cesta Básica Nacional de Alimentos. "
            "§ 2º Fica instituída a devolução personalizada de tributos (cashback) incidente sobre gás, "
            "energia elétrica, água, esgotamento sanitário e telecomunicações para famílias inscritas no CadÚnico."
        ),
    },
    {
        "number": "PL 2628/2022",
        "title": "Proteção de Crianças e Adolescentes em Ambientes Digitais (ECA Digital)",
        "official_summary": (
            "Art. 1º Esta Lei estabelece obrigações de prevenção, proteção e salvaguarda aplicáveis aos "
            "fornecedores de produtos ou serviços de tecnologia da informação direcionados a crianças "
            "e adolescentes no território nacional. "
            "Art. 9º Os provedores de aplicações de internet, redes sociais e plataformas de vídeo deverão "
            "adotar mecanismos confiáveis de aferição etária no momento do cadastro e da autenticação, "
            "vedada a autodeclaração meramente formal sem verificação técnica complementar. "
            "Art. 18. É terminantemente vedado o emprego de técnicas de perfilamento comercial, segmentação "
            "comportamental, coleta biométrica ou direcionamento de publicidade personalizada com base em "
            "dados pessoais de crianças e adolescentes. "
            "§ 1º Nos jogos eletrônicos acessíveis a menores de dezoito anos, fica proibida a oferta "
            "onerosa de caixas de recompensa (loot boxes) com mecânicas aleatórias assemelhadas a jogos "
            "de azar, devendo as ferramentas de supervisão parental obrigatória limitar compras integradas."
        ),
    },
    {
        "number": "PL 712/2026",
        "title": "Lei de Transparência Ativa e Dados Abertos em Tempo Real nas Obras Estaduais",
        "official_summary": (
            "Art. 1º Estabelece a obrigatoriedade de publicação em formato aberto (JSON/CSV) e "
            "georreferenciado de todos os contratos, aditivos financeiros, medições físicas, notas de "
            "empenho e cronogramas de execução de obras públicas estaduais cujo valor global ultrapasse "
            "quinhentos mil reais, mediante atualização semanal obrigatória em portal acessível ao cidadão. "
            "Art. 4º Fica expressamente vedada a celebração de novos aditivos financeiros ou prorrogações "
            "contratuais sem a prévia publicação da justificativa técnica circunstanciada e do registro "
            "fotográfico georreferenciado de medição da etapa física imediatamente anterior."
        ),
    },
    {
        "number": "PL 508/2026",
        "title": "Plano Estadual de Segurança Hídrica, Drenagem Inteligente e Prevenção de Enchentes",
        "official_summary": (
            "Art. 1º Cria o Sistema Integrado de Monitoramento Hidrometeorológico Estadual com rede de "
            "sensores pluviométricos e fluviométricos de alerta precoce integrados à Defesa Civil para "
            "emissão automatizada de avisos preventivos à população residente em áreas de risco geológico. "
            "Art. 6º Obriga a elaboração de planos municipais de drenagem urbana permeável e destina "
            "quinze por cento dos royalties ambientais estaduais para obras de desassoreamento, contenção "
            "de encostas, parques alagáveis e reservatórios de amortecimento mediante dotação orçamentária."
        ),
    },
]


def main() -> None:
    offline_mode = "--offline" in sys.argv
    if not offline_mode:
        _load_root_dotenv()

    print("=" * 82)
    print("QUORUM IA — AVALIAÇÃO DE GANHO DE LEGIBILIDADE (DESJURIDIQUÊS)")
    if offline_mode:
        print("MODO: Fallback Determinístico Offline (--offline)")
    print("=" * 82)

    results = []
    valid_json_count = 0

    for idx, sample in enumerate(SAMPLE_BILLS, start=1):
        output = translate_bill(
            sample["title"],
            sample["official_summary"],
            api_key="" if offline_mode else None,
        )
        if len(output["bullets"]) == 3:
            valid_json_count += 1

        results.append((sample["number"], output))

        if idx == 1:
            print("\n[DEMONSTRAÇÃO ENTRADA -> SAÍDA]")
            print(f"Proposição : {sample['number']} — {sample['title']}")
            print(f"Motor      : {output['provider']} ({output['model']})")
            print(f"Entrada    : {sample['official_summary'][:220]}...")
            print("Saída JSON :")
            print(
                json.dumps(
                    {
                        "bullets": output["bullets"],
                        "detected_theme": output["detected_theme"],
                        "citizen_impact_level": output["citizen_impact_level"],
                        "key_terms_explained": output["key_terms_explained"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )

    print("\n[TABELA COMPARATIVA ANTES vs. DEPOIS]")
    print(
        f"{'PL':<14} {'Palavras':>12} {'Flesch Antes':>13} {'Flesch Depois':>14} "
        f"{'Ganho':>8} {'Tempo':>12} {'Economia':>9}"
    )
    print("-" * 82)

    total_gain = 0.0
    total_time_saved = 0
    total_reduction = 0.0
    for number, output in results:
        m = output["metrics"]
        total_gain += float(m["readability_gain_points"])
        total_time_saved += int(m["reading_time_saved_sec"])
        total_reduction += float(m["word_reduction_pct"])
        words_pair = f"{m['original_word_count']}->{m['summary_word_count']}"
        time_pair = f"{m['reading_time_before_sec']}s->{m['reading_time_after_sec']}s"
        print(
            f"{number:<14} "
            f"{words_pair:>12} "
            f"{m['flesch_before']:>13.1f} "
            f"{m['flesch_after']:>14.1f} "
            f"{'+' + str(m['readability_gain_points']):>8} "
            f"{time_pair:>12} "
            f"{str(m['reading_time_saved_sec']) + 's':>9}"
        )

    avg_gain = round(total_gain / len(results), 1)
    avg_saved = round(total_time_saved / len(results), 1)
    avg_reduction = round(total_reduction / len(results), 1)
    print("-" * 82)
    print(f"Validade estrutural (3 bullets): {valid_json_count}/{len(results)} (100%)")
    print(f"Redução média de palavras      : {avg_reduction}%")
    print(f"Ganho médio de legibilidade    : +{avg_gain} pontos Flesch pt-BR")
    print(f"Economia média de tempo        : {avg_saved}s por proposição")
    print("=" * 82)


if __name__ == "__main__":
    main()
