tradevision-ai/
├── backend/
│   ├── app/
│   │   ├── api/                 # presentation layer — routers
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── ocr.py
│   │   │       ├── market.py
│   │   │       ├── reports.py
│   │   │       ├── chat.py
│   │   │       └── history.py
│   │   ├── services/             # application layer — business logic
│   │   │   ├── ocr_service.py
│   │   │   ├── market_service.py
│   │   │   ├── technical_analysis_service.py
│   │   │   ├── news_service.py
│   │   │   ├── risk_service.py
│   │   │   └── llm_service.py
│   │   ├── domain/                # domain layer — entities, interfaces
│   │   │   ├── models.py
│   │   │   └── schemas.py         # Pydantic request/response models
│   │   ├── infrastructure/        # infra layer — DB, external clients
│   │   │   ├── db/
│   │   │   │   ├── session.py
│   │   │   │   └── repositories/
│   │   │   ├── external/
│   │   │   │   ├── twelve_data_client.py
│   │   │   │   └── finnhub_client.py
│   │   │   └── llm/
│   │   │       └── openai_client.py
│   │   ├── core/                  # config, security, logging
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   └── main.py
│   ├── alembic/                   # migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                       # Next.js app router
│   │   ├── (auth)/login/
│   │   ├── (auth)/register/
│   │   ├── dashboard/
│   │   ├── upload/
│   │   ├── analysis/[id]/
│   │   ├── history/
│   │   └── settings/
│   ├── components/
│   │   ├── ui/                    # shadcn components
│   │   ├── charts/
│   │   └── layout/
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── validators.ts          # Zod schemas
│   ├── hooks/
│   └── Dockerfile
├── docs/
│   ├── architecture.md
│   └── erd.md
├── docker-compose.yml
└── README.md