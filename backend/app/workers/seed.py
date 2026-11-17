from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.legislative import (
    Bill,
    LegislativeHouse,
    OfficialVote,
    Party,
    Politician,
    RawLegislativeEvent,
)

SEED_HOUSES = [
    {
        "name": "Congresso Nacional (Câmara dos Deputados)",
        "short_name": "Congresso Nacional",
        "slug": "congresso-nacional",
        "level": "federal",
        "state_or_city": "Brasília - DF",
        "total_seats": 513,
        "followers_count": 148200,
        "is_followed_by_default": True,
        "official_portal_url": "https://www.camara.leg.br",
        "description": (
            "Casa responsável pela discussão e votação de leis federais, orçamento da União "
            "e fiscalização do Poder Executivo em todo o território nacional."
        ),
        "upcoming_sessions": [
            {
                "id": "sess-cn-1",
                "date": "Hoje",
                "time": "16:00",
                "title": "Sessão Deliberativa Extraordinária — Plenário Ulysses Guimarães",
                "type": "Votação em Plenário",
                "highlighted_bills": ["PL 1420/2026"],
            },
            {
                "id": "sess-cn-2",
                "date": "Quinta-feira, 19/11",
                "time": "10:00",
                "title": "Comissão de Desenvolvimento Urbano — Debate sobre Corredores Verdes",
                "type": "Comissão Temática",
                "highlighted_bills": ["PL 1420/2026"],
            },
        ],
        "party_composition_json": [
            {"party": "PL", "party_name": "Partido Liberal", "seat_count": 99, "color_hex": "#1D4ED8"},
            {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 68, "color_hex": "#DC2626"},
            {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 59, "color_hex": "#0284C7"},
            {"party": "PP", "party_name": "Progressistas", "seat_count": 50, "color_hex": "#2563EB"},
            {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 44, "color_hex": "#009C3B"},
            {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 44, "color_hex": "#EAB308"},
            {"party": "PSB", "party_name": "Partido Socialista Brasileiro", "seat_count": 15, "color_hex": "#EA580C"},
            {"party": "PSOL", "party_name": "Partido Socialismo e Liberdade", "seat_count": 13, "color_hex": "#9333EA"},
            {"party": "NOVO", "party_name": "Partido Novo", "seat_count": 4, "color_hex": "#F97316"},
            {"party": "Outros", "party_name": "Demais Partidos e Federações", "seat_count": 117, "color_hex": "#64748B"},
        ],
    },
    {
        "name": "Senado Federal",
        "short_name": "Senado Federal",
        "slug": "senado-federal",
        "level": "federal",
        "state_or_city": "Brasília - DF",
        "total_seats": 81,
        "followers_count": 112400,
        "is_followed_by_default": True,
        "official_portal_url": "https://www12.senado.leg.br",
        "description": (
            "Câmara Alta do Congresso Nacional responsável pela revisão de projetos federais, "
            "equilíbrio federativo entre os estados e sabatinas institucionais."
        ),
        "upcoming_sessions": [
            {
                "id": "sess-sf-1",
                "date": "Amanhã, 17/11",
                "time": "15:00",
                "title": "Plenário do Senado — Votação do Marco de Auditoria Digital em Compras",
                "type": "Sessão Deliberativa",
                "highlighted_bills": ["PL 118/2026"],
            },
            {
                "id": "sess-sf-2",
                "date": "Quinta-feira, 19/11",
                "time": "10:00",
                "title": "Comissão de Infraestrutura — Microgeração Solar em Habitações Sociais",
                "type": "Comissão Temática",
                "highlighted_bills": ["PL 2905/2026"],
            },
        ],
        "party_composition_json": [
            {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 15, "color_hex": "#EAB308"},
            {"party": "PL", "party_name": "Partido Liberal", "seat_count": 14, "color_hex": "#1D4ED8"},
            {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 11, "color_hex": "#009C3B"},
            {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 9, "color_hex": "#DC2626"},
            {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 7, "color_hex": "#0284C7"},
            {"party": "PP", "party_name": "Progressistas", "seat_count": 7, "color_hex": "#2563EB"},
            {"party": "PSB", "party_name": "Partido Socialista Brasileiro", "seat_count": 4, "color_hex": "#EA580C"},
            {"party": "NOVO", "party_name": "Partido Novo", "seat_count": 1, "color_hex": "#F97316"},
            {"party": "Outros", "party_name": "Demais Partidos e Blocos", "seat_count": 13, "color_hex": "#64748B"},
        ],
    },
    {
        "name": "Assembleia Legislativa do Estado de São Paulo (ALESP)",
        "short_name": "ALESP",
        "slug": "alesp",
        "level": "state",
        "state_or_city": "São Paulo - SP",
        "total_seats": 94,
        "followers_count": 64500,
        "is_followed_by_default": False,
        "official_portal_url": "https://www.al.sp.gov.br",
        "description": (
            "Parlamento paulista encarregado de aprovar leis estaduais, diretrizes de infraestrutura, "
            "transparência pública e fiscalização do governo do Estado de São Paulo."
        ),
        "upcoming_sessions": [
            {
                "id": "sess-alesp-1",
                "date": "Quarta-feira, 18/11",
                "time": "14:30",
                "title": "Ordem do Dia — Avaliação de Vetos e Regulamentação de Dados Abertos",
                "type": "Sessão Ordinária",
                "highlighted_bills": ["PL 712/2026", "PL 904/2026"],
            }
        ],
        "party_composition_json": [
            {"party": "PL", "party_name": "Partido Liberal", "seat_count": 19, "color_hex": "#1D4ED8"},
            {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 18, "color_hex": "#DC2626"},
            {"party": "REPUBLICANOS", "party_name": "Republicanos", "seat_count": 8, "color_hex": "#0284C7"},
            {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 8, "color_hex": "#2563EB"},
            {"party": "PSOL", "party_name": "Partido Socialismo e Liberdade", "seat_count": 5, "color_hex": "#9333EA"},
            {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 4, "color_hex": "#009C3B"},
            {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 4, "color_hex": "#EAB308"},
            {"party": "PSB", "party_name": "Partido Socialista Brasileiro", "seat_count": 3, "color_hex": "#EA580C"},
            {"party": "NOVO", "party_name": "Partido Novo", "seat_count": 2, "color_hex": "#F97316"},
            {"party": "Outros", "party_name": "Demais Partidos", "seat_count": 23, "color_hex": "#64748B"},
        ],
    },
    {
        "name": "Câmara Municipal de São Paulo (CMSP)",
        "short_name": "Câmara Municipal de SP",
        "slug": "cmsp",
        "level": "municipal",
        "state_or_city": "São Paulo - SP",
        "total_seats": 55,
        "followers_count": 53900,
        "is_followed_by_default": False,
        "official_portal_url": "https://www.saopaulo.sp.leg.br",
        "description": (
            "Poder Legislativo da capital paulista, responsável por políticas de transporte coletivo, "
            "plano diretor, zeladoria urbana e orçamento municipal."
        ),
        "upcoming_sessions": [
            {
                "id": "sess-cmsp-1",
                "date": "Amanhã, 17/11",
                "time": "14:30",
                "title": "Plenário 1º de Maio — 2ª Votação do Programa Tarifa Zero Integrada",
                "type": "Sessão Plenária",
                "highlighted_bills": ["PL 389/2026"],
            }
        ],
        "party_composition_json": [
            {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 8, "color_hex": "#DC2626"},
            {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 7, "color_hex": "#009C3B"},
            {"party": "PL", "party_name": "Partido Liberal", "seat_count": 7, "color_hex": "#1D4ED8"},
            {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 7, "color_hex": "#0284C7"},
            {"party": "PSOL", "party_name": "Partido Socialismo e Liberdade", "seat_count": 6, "color_hex": "#9333EA"},
            {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 4, "color_hex": "#EAB308"},
            {"party": "PSB", "party_name": "Partido Socialista Brasileiro", "seat_count": 3, "color_hex": "#EA580C"},
            {"party": "NOVO", "party_name": "Partido Novo", "seat_count": 2, "color_hex": "#F97316"},
            {"party": "Outros", "party_name": "Demais Bancadas", "seat_count": 11, "color_hex": "#64748B"},
        ],
    },
    {
        "name": "Assembleia Legislativa do Estado do Rio de Janeiro (ALERJ)",
        "short_name": "ALERJ",
        "slug": "alerj",
        "level": "state",
        "state_or_city": "Rio de Janeiro - RJ",
        "total_seats": 70,
        "followers_count": 41200,
        "is_followed_by_default": False,
        "official_portal_url": "https://www.alerj.rj.gov.br",
        "description": (
            "Casa legislativa fluminense dedicada a leis estaduais de segurança hídrica, "
            "transição climática, saneamento e proteção civil."
        ),
        "upcoming_sessions": [
            {
                "id": "sess-alerj-1",
                "date": "Hoje",
                "time": "18:00",
                "title": "Plenário Barbosa Lima Sobrinho — Votação de Urgência em Drenagem Urbana",
                "type": "Sessão Extraordinária",
                "highlighted_bills": ["PL 508/2026"],
            }
        ],
        "party_composition_json": [
            {"party": "PL", "party_name": "Partido Liberal", "seat_count": 17, "color_hex": "#1D4ED8"},
            {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 8, "color_hex": "#0284C7"},
            {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 7, "color_hex": "#DC2626"},
            {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 6, "color_hex": "#EAB308"},
            {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 5, "color_hex": "#009C3B"},
            {"party": "PSOL", "party_name": "Partido Socialismo e Liberdade", "seat_count": 5, "color_hex": "#9333EA"},
            {"party": "PSB", "party_name": "Partido Socialista Brasileiro", "seat_count": 3, "color_hex": "#EA580C"},
            {"party": "Outros", "party_name": "Demais Partidos", "seat_count": 19, "color_hex": "#64748B"},
        ],
    },
]

SEED_PARTIES = [
    {
        "acronym": "PSB",
        "name": "Partido Socialista Brasileiro",
        "color_hex": "#EA580C",
        "registration_number": 40,
        "foundation_year": 1947,
        "spectrum": "Centro-esquerda",
        "program_summary": (
            "Atuação parlamentar voltada à mobilidade sustentável, reindustrialização verde, "
            "educação pública e desenvolvimento urbano com justiça social."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "NOVO",
        "name": "Partido Novo",
        "color_hex": "#F97316",
        "registration_number": 30,
        "foundation_year": 2011,
        "spectrum": "Direita",
        "program_summary": (
            "Agenda parlamentar focada em transparência fiscal, governo digital aberto, "
            "desburocratização administrativa e controle de gastos públicos."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "PSOL",
        "name": "Partido Socialismo e Liberdade",
        "color_hex": "#9333EA",
        "registration_number": 50,
        "foundation_year": 2004,
        "spectrum": "Esquerda",
        "program_summary": (
            "Prioriza tarifa zero no transporte coletivo, direito à cidade, democratização "
            "dos serviços públicos e transição ecológica popular."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "MDB",
        "name": "Movimento Democrático Brasileiro",
        "color_hex": "#009C3B",
        "registration_number": 15,
        "foundation_year": 1980,
        "spectrum": "Centro",
        "program_summary": (
            "Bancada com atuação municipalista, infraestrutura energética, pacto federativo "
            "e políticas de desenvolvimento regional."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "PSD",
        "name": "Partido Social Democrático",
        "color_hex": "#EAB308",
        "registration_number": 55,
        "foundation_year": 2011,
        "spectrum": "Centro",
        "program_summary": (
            "Foco em gestão municipal e estadual, segurança hídrica, infraestrutura de "
            "saneamento básico e eficiência administrativa."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "PT",
        "name": "Partido dos Trabalhadores",
        "color_hex": "#DC2626",
        "registration_number": 13,
        "foundation_year": 1980,
        "spectrum": "Centro-esquerda",
        "program_summary": (
            "Defesa da educação pública conectada, ampliação de direitos sociais, inclusão "
            "digital e participação cidadã no orçamento público."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "PL",
        "name": "Partido Liberal",
        "color_hex": "#1D4ED8",
        "registration_number": 22,
        "foundation_year": 2006,
        "spectrum": "Direita",
        "program_summary": (
            "Maior bancada na Câmara dos Deputados e ALESP na legislatura vigente, com "
            "pautas econômicas liberais e de segurança pública."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
    {
        "acronym": "UNIÃO",
        "name": "União Brasil",
        "color_hex": "#0284C7",
        "registration_number": 44,
        "foundation_year": 2021,
        "spectrum": "Centro-direita",
        "program_summary": (
            "Atuação parlamentar concentrada em desenvolvimento regional, reforma "
            "administrativa, segurança pública e competitividade."
        ),
        "official_portal_url": "https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    },
]

SEED_POLITICIANS = [
    {
        "external_id": "camara-204521",
        "house_slug": "congresso-nacional",
        "party_acronym": "PSB",
        "name": "Dep. Helena Vasconcelos",
        "state": "SP",
        "role": "Deputada Federal",
        "legislature": "57ª Legislatura (2023–2027)",
        "attendance_rate": "96,4% em sessões deliberativas",
        "biography_summary": (
            "Engenheira civil especializada em planejamento urbano e transporte público "
            "sustentável. Vice-presidente da Comissão de Viação e Transportes."
        ),
        "official_portal_url": "https://www.camara.leg.br/deputados/204521",
    },
    {
        "external_id": "senado-204890",
        "house_slug": "senado-federal",
        "party_acronym": "MDB",
        "name": "Sen. Marcos Vinícius Rocha",
        "state": "MG",
        "role": "Senador da República",
        "legislature": "57ª Legislatura (2023–2031)",
        "attendance_rate": "92,7% em sessões deliberativas",
        "biography_summary": (
            "Engenheiro eletricista e ex-secretário estadual de energia renovável. Relator "
            "de propostas voltadas à geração solar distribuída e transparência em compras públicas."
        ),
        "official_portal_url": "https://www25.senado.leg.br/web/senadores/em-exercicio",
    },
    {
        "external_id": "alesp-300812",
        "house_slug": "alesp",
        "party_acronym": "NOVO",
        "name": "Dep. Ricardo Alencar",
        "state": "SP",
        "role": "Deputado Estadual",
        "legislature": "20ª Legislatura (2023–2027)",
        "attendance_rate": "98,1% em sessões plenárias",
        "biography_summary": (
            "Administrador público e auditor de contas. Atua na Comissão de Finanças, "
            "Orçamento e Planejamento com foco em eficiência fiscal e governo digital."
        ),
        "official_portal_url": "https://www.al.sp.gov.br/deputado/?matricula=300812",
    },
    {
        "external_id": "cmsp-190012",
        "house_slug": "cmsp",
        "party_acronym": "PSOL",
        "name": "Ver. Lucas Moura Lima",
        "state": "SP",
        "role": "Vereador",
        "legislature": "19ª Legislatura (2025–2028)",
        "attendance_rate": "94,8% em sessões ordinárias",
        "biography_summary": (
            "Geógrafo e pesquisador de mobilidade periférica. Integrante da Comissão de "
            "Política Urbana, Metropolitana e Meio Ambiente."
        ),
        "official_portal_url": "https://www.saopaulo.sp.leg.br/vereador/lucas-moura-lima",
    },
    {
        "external_id": "alerj-130410",
        "house_slug": "alerj",
        "party_acronym": "PSD",
        "name": "Dep. Beatriz Cavalcanti",
        "state": "RJ",
        "role": "Deputada Estadual",
        "legislature": "13ª Legislatura (2023–2027)",
        "attendance_rate": "95,5% em sessões plenárias",
        "biography_summary": (
            "Hidróloga e especialista em defesa civil comunitária. Presidente da Comissão "
            "Especial de Adaptação Climática e Segurança Hídrica da ALERJ."
        ),
        "official_portal_url": "https://www.alerj.rj.gov.br/Deputados/Perfil/beatriz-cavalcanti",
    },
    {
        "external_id": "alesp-300945",
        "house_slug": "alesp",
        "party_acronym": "PT",
        "name": "Dep. Carlos Eduardo Nogueira",
        "state": "SP",
        "role": "Deputado Estadual",
        "legislature": "20ª Legislatura (2023–2027)",
        "attendance_rate": "97,0% em sessões plenárias",
        "biography_summary": (
            "Professor da rede pública estadual e mestre em políticas educacionais. Membro "
            "titular da Comissão de Educação e Cultura da ALESP."
        ),
        "official_portal_url": "https://www.al.sp.gov.br/deputado/?matricula=300945",
    },
]

SEED_BILLS = [
    {
        "external_id": "pl-1420-2026",
        "house_slug": "congresso-nacional",
        "author_external_id": "camara-204521",
        "number": "PL 1420/2026",
        "year": 2026,
        "title": "Marco Nacional da Mobilidade Urbana Sustentável e Corredores Verdes",
        "theme": "Mobilidade Urbana",
        "official_summary": (
            "Institui diretrizes gerais para a integração intermodal de corredores exclusivos "
            "de transporte público de baixa emissão, estabelece metas de eletrificação da frota "
            "municipal acima de 100 mil habitantes e vincula repasses federais de mobilidade ao "
            "cumprimento de acessibilidade universal em calçadas e terminais."
        ),
        "desjuridiques_summary": [
            "Garante prioridade de repasse federal para cidades que criarem faixas exclusivas de ônibus elétricos e ciclovias integradas ao metrô ou trem.",
            "Obriga novos terminais e pontos de ônibus a terem piso tátil, rampas acessíveis e cobertura contra chuva e calor extremo.",
            "Prevê meta de redução de 35% no tempo médio de deslocamento casa-trabalho nas regiões metropolitanas até 2030.",
        ],
        "status": "Votação Agendada",
        "next_vote_at": "Hoje, 16:00",
        "is_urgent_vote": True,
        "likes_count": 4390,
        "votes_favor": 12840,
        "votes_against": 2160,
        "official_approval_rate": 78,
    },
    {
        "external_id": "pl-389-2026",
        "house_slug": "cmsp",
        "author_external_id": "cmsp-190012",
        "number": "PL 389/2026",
        "year": 2026,
        "title": "Programa Tarifa Zero Integrada aos Domingos, Feriados e Horários de Vale",
        "theme": "Tarifa de Transporte Público",
        "official_summary": (
            "Dispõe sobre a ampliação da gratuidade no Sistema de Transporte Coletivo Urbano de "
            "Passageiros por Ônibus aos domingos, feriados nacionais e faixa horária entre 10h e 15h "
            "em dias úteis, mediante compensação pelo Fundo Municipal de Mobilidade."
        ),
        "desjuridiques_summary": [
            "Mantém passagem gratuita aos domingos e feriados e cria gratuidade nos ônibus entre 10h e 15h de segunda a sexta-feira.",
            "O financiamento vem do fundo de multas de trânsito e de parte da arrecadação da Zona Azul digital, sem aumentar o IPTU.",
            "Beneficia diretamente trabalhadores informais, estudantes e idosos que precisam se deslocar fora do horário de pico.",
        ],
        "status": "Votação Agendada",
        "next_vote_at": "Amanhã, 14:30",
        "is_urgent_vote": True,
        "likes_count": 3810,
        "votes_favor": 9420,
        "votes_against": 3180,
        "official_approval_rate": 62,
    },
    {
        "external_id": "pl-712-2026",
        "house_slug": "alesp",
        "author_external_id": "alesp-300812",
        "number": "PL 712/2026",
        "year": 2026,
        "title": "Lei de Transparência Ativa e Dados Abertos em Tempo Real nas Obras Estaduais",
        "theme": "Transparência e Dados Abertos",
        "official_summary": (
            "Estabelece a obrigatoriedade de publicação em formato aberto (JSON/CSV) e "
            "georreferenciado de todos os contratos, aditivos financeiros, medições físicas "
            "e cronogramas de execução de obras públicas estaduais acima de 500 mil reais."
        ),
        "desjuridiques_summary": [
            "Qualquer cidadão poderá acompanhar pela internet o andamento real, o valor pago e eventuais atrasos de obras acima de R$ 500 mil.",
            "Os dados devem ser publicados em formato aberto e atualizado semanalmente, permitindo auditoria automática por pesquisadores e aplicativos cívicos.",
            "Proíbe novos aditivos de verba sem a publicação prévia da justificativa técnica e das fotos de medição da etapa anterior.",
        ],
        "status": "Aprovado",
        "next_vote_at": "Aprovado em 08/11/2026",
        "is_urgent_vote": False,
        "likes_count": 6240,
        "votes_favor": 15640,
        "votes_against": 890,
        "official_approval_rate": 91,
    },
    {
        "external_id": "pl-2905-2026",
        "house_slug": "senado-federal",
        "author_external_id": "senado-204890",
        "number": "PL 2905/2026",
        "year": 2026,
        "title": "Programa Energia Solar Social e Microgeração em Habitações Populares",
        "theme": "Incentivo à Energia Solar",
        "official_summary": (
            "Institui linha de subvenção econômica e isenção de tributos federais incidentes sobre "
            "inversores e módulos fotovoltaicos destinados a conjuntos habitacionais de interesse "
            "social e cooperativas de energia comunitária."
        ),
        "desjuridiques_summary": [
            "Zera impostos federais sobre placas solares e inversores instalados em moradias populares e cooperativas de bairros.",
            "Famílias inscritas no CadÚnico podem reduzir a conta de luz em até 70% usando créditos compartilhados de energia solar.",
            "Inclui capacitação técnica gratuita para jovens da própria comunidade trabalharem na instalação e manutenção dos painéis.",
        ],
        "status": "Em Tramitação",
        "next_vote_at": "24/11/2026, 10:00 (Comissão)",
        "is_urgent_vote": False,
        "likes_count": 3920,
        "votes_favor": 11200,
        "votes_against": 1450,
        "official_approval_rate": 74,
    },
    {
        "external_id": "pl-118-2026",
        "house_slug": "senado-federal",
        "author_external_id": "senado-204890",
        "number": "PL 118/2026",
        "year": 2026,
        "title": "Marco de Transparência em Compras Públicas e Auditoria Digital",
        "theme": "Transparência e Contratos Públicos",
        "official_summary": (
            "Dispõe sobre a padronização nacional dos portais de compras governamentais em API "
            "aberta, exigindo trilha de auditoria em tempo real para dispensas de licitação e "
            "comparativo automático de preços de referência."
        ),
        "desjuridiques_summary": [
            "Obriga órgãos públicos de todo o país a publicarem em tempo real os contratos sem licitação e os valores pagos por cada item.",
            "Compara automaticamente o preço contratado com a média de mercado para alertar sobre superfaturamento antes do pagamento.",
            "Libera consulta gratuita em dados abertos para jornalistas, tribunais de contas e cidadãos.",
        ],
        "status": "Votação Agendada",
        "next_vote_at": "Amanhã, 15:00",
        "is_urgent_vote": True,
        "likes_count": 5480,
        "votes_favor": 14350,
        "votes_against": 920,
        "official_approval_rate": 86,
    },
    {
        "external_id": "pl-508-2026",
        "house_slug": "alerj",
        "author_external_id": "alerj-130410",
        "number": "PL 508/2026",
        "year": 2026,
        "title": "Plano Estadual de Segurança Hídrica, Drenagem Inteligente e Prevenção de Enchentes",
        "theme": "Segurança Hídrica e Clima",
        "official_summary": (
            "Cria o Sistema Integrado de Monitoramento Hidrometeorológico Estadual com rede de "
            "sensores pluviométricos de alerta precoce e destina 15% dos royalties ambientais para "
            "obras de contenção de encostas e reservatórios de amortecimento."
        ),
        "desjuridiques_summary": [
            "Instala sensores de nível de rios e chuvas integrados à Defesa Civil para enviar alertas antecipados por SMS antes de alagamentos.",
            "Reserva 15% dos recursos ambientais do estado para desassoreamento de rios, parques alagáveis e contenção de encostas em áreas de risco.",
            "Exige que novas obras viárias estaduais utilizem piso drenante para evitar enxurradas e proteger o abastecimento de água.",
        ],
        "status": "Votação Agendada",
        "next_vote_at": "Hoje, 18:00",
        "is_urgent_vote": True,
        "likes_count": 3150,
        "votes_favor": 8740,
        "votes_against": 1120,
        "official_approval_rate": 84,
    },
    {
        "external_id": "pl-904-2026",
        "house_slug": "alesp",
        "author_external_id": "alesp-300945",
        "number": "PL 904/2026",
        "year": 2026,
        "title": "Programa Escolas Conectadas e Proteção de Dados de Estudantes na Rede Pública",
        "theme": "Conectividade e Educação Digital",
        "official_summary": (
            "Assegura conectividade de banda larga por fibra óptica com redundância em 100% das "
            "escolas estaduais e veda a comercialização ou compartilhamento de dados pessoais e "
            "biométricos de estudantes menores de idade."
        ),
        "desjuridiques_summary": [
            "Garante internet de alta velocidade em todas as escolas públicas estaduais, priorizando zonas rurais e bairros periféricos.",
            "Proíbe empresas de software escolar de venderem ou usarem dados de alunos para publicidade ou treinamento comercial.",
            "Cria painel público mensal mostrando a velocidade real da internet entregue em cada unidade escolar.",
        ],
        "status": "Aprovado",
        "next_vote_at": "Aprovado em 03/11/2026",
        "is_urgent_vote": False,
        "likes_count": 5110,
        "votes_favor": 13190,
        "votes_against": 1040,
        "official_approval_rate": 88,
    },
]

SEED_OFFICIAL_VOTES = [
    ("pl-1420-2026", "camara-204521", "Sim", "12/11/2026 (Comissão)"),
    ("pl-2905-2026", "camara-204521", "Sim", "05/11/2026 (Relatoria)"),
    ("pl-712-2026", "camara-204521", "Sim", "22/10/2026"),
    ("pl-118-2026", "senado-204890", "Sim", "11/11/2026 (Comissão)"),
    ("pl-2905-2026", "senado-204890", "Sim", "05/11/2026 (Comissão)"),
    ("pl-1420-2026", "senado-204890", "Não", "12/11/2026 (Comissão)"),
    ("pl-712-2026", "alesp-300812", "Sim", "08/11/2026"),
    ("pl-904-2026", "alesp-300812", "Sim", "03/11/2026"),
    ("pl-389-2026", "alesp-300812", "Não", "19/10/2026"),
    ("pl-389-2026", "cmsp-190012", "Sim", "10/11/2026 (1º Turno)"),
    ("pl-1420-2026", "cmsp-190012", "Sim", "29/10/2026"),
    ("pl-508-2026", "alerj-130410", "Sim", "11/11/2026 (Comissão de Orçamento)"),
    ("pl-712-2026", "alerj-130410", "Sim", "27/10/2026"),
    ("pl-904-2026", "alesp-300945", "Sim", "03/11/2026"),
    ("pl-712-2026", "alesp-300945", "Sim", "08/11/2026"),
]


def seed_database(db: Session) -> None:
    """Populate initial Bronze and Silver legislative data if the database is empty."""
    existing_house = db.scalar(select(LegislativeHouse.id).limit(1))
    if existing_house is not None:
        return

    house_map: dict[str, LegislativeHouse] = {}
    for item in SEED_HOUSES:
        house = LegislativeHouse(**item)
        db.add(house)
        db.flush()
        house_map[house.slug] = house

    party_map: dict[str, Party] = {}
    for item in SEED_PARTIES:
        party = Party(**item)
        db.add(party)
        db.flush()
        party_map[party.acronym] = party

    politician_map: dict[str, Politician] = {}
    for item in SEED_POLITICIANS:
        house = house_map[item["house_slug"]]
        party = party_map[item["party_acronym"]]
        politician = Politician(
            external_id=item["external_id"],
            house_id=house.id,
            party_id=party.id,
            name=item["name"],
            state=item["state"],
            role=item["role"],
            legislature=item["legislature"],
            attendance_rate=item["attendance_rate"],
            biography_summary=item["biography_summary"],
            official_portal_url=item["official_portal_url"],
            is_active=True,
        )
        db.add(politician)
        db.flush()
        politician_map[politician.external_id] = politician

    bill_map: dict[str, Bill] = {}
    for item in SEED_BILLS:
        house = house_map[item["house_slug"]]
        author = politician_map.get(item["author_external_id"])
        bill = Bill(
            external_id=item["external_id"],
            house_id=house.id,
            author_id=author.id if author else None,
            number=item["number"],
            year=item["year"],
            title=item["title"],
            theme=item["theme"],
            official_summary=item["official_summary"],
            desjuridiques_summary=item["desjuridiques_summary"],
            status=item["status"],
            next_vote_at=item["next_vote_at"],
            is_urgent_vote=item["is_urgent_vote"],
            likes_count=item["likes_count"],
            votes_favor=item["votes_favor"],
            votes_against=item["votes_against"],
            official_approval_rate=item["official_approval_rate"],
        )
        db.add(bill)
        db.flush()
        bill_map[bill.external_id] = bill

        # Mirror initial bill creation into Bronze raw_legislative_events
        db.add(
            RawLegislativeEvent(
                source="seed_bootstrap",
                entity_type="bill",
                external_id=bill.external_id,
                raw_payload={
                    "number": bill.number,
                    "title": bill.title,
                    "house_slug": item["house_slug"],
                },
            )
        )

    for bill_ext_id, pol_ext_id, choice, date_label in SEED_OFFICIAL_VOTES:
        bill = bill_map.get(bill_ext_id)
        politician = politician_map.get(pol_ext_id)
        if bill and politician:
            db.add(
                OfficialVote(
                    bill_id=bill.id,
                    politician_id=politician.id,
                    vote_choice=choice,
                    date_label=date_label,
                )
            )

    db.commit()
