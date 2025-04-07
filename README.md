## 

1. POST - `/api/v1/calculate/` - сделать расчет календарного плана

Body:
  
```json
{
  // Цены
  "directory": {
    // Цены бетона по классам
    "concrete_classes": [
      {
        "name": "string",
        "price": 0
      }
    ],
    // Цена проволоки
    "wire": {
      "price": 0
    },
    // Цена переналадки машины  для залива
    "retooling": {
      "price": 0
    },
    // длина дорожки
    "track": {
      "length": 0
    }
  },
  // Настройки машины для залива
  "retooler":{
    "height": 0,
    "width": 0
  },
   // Готовые плиты
  "ready_plates": [
    {
      "count": 0,
      "length": 0,
      "width": 0,
      "height": 0,
      "class": "string", // Класс бетона
      "wire_bottom": 0, // Проволока снизу
      "wire_top": 0 // Проволока сверху
    }
  ],
  // Свободные дорожки
  "available_tracks": [
    {
      "count": 0,
      "day": "2025-03-18"
    }
  ],
  // Заказы
  "orders": [
    {
      "number": "string",
      "production_days": 0,
      "completion_dates": [
        {
          "date": "2025-03-18", // Дата к которой нужны плиты
          "plates": [
            {
              "count": 0,
              "length": 0,
              "width": 0,
              "height": 0,
              "class": "string", // Класс бетона
              "wire_bottom": 0, // Проволока снизу
              "wire_top": 0 // Проволока сверху
            }
          ]
        }
      ]
    }
  ]
}
```

## Response
## В финальном варианте изменится
### status code `200`:

```json
{
  "calendar_plan": {
    "directories": {
      "concrete_classes": [
        {
          "name": "B25",
          "price": 6600
        },
        {
          "name": "B30",
          "price": 6800
        }
      ],
      "wire": {
        "price": 15.1
      },
      "retooling": {
        "price": 15000
      },
      "production_track": {
        "length": 85000
      }
    },
    "suitable_ready_plates": [
      {
        "count": 1,
        "length": 2800,
        "width": 1000,
        "height": 220,
        "concrete_class": "B25",
        "wire_top": 4,
        "wire_bottom": 4
      }
    ],
    "remaining_ready_plates": [
      {
        "count": 1,
        "length": 2800,
        "width": 1000,
        "height": 240,
        "concrete_class": "B25",
        "wire_top": 4,
        "wire_bottom": 4
      }
    ],
    "days": [
      {
        "date": "2025-01-17",
        "tracks": [
          {
            "width": 1200,
            "height": 220,
            "concrete_class": "B25",
            "wire_top": 4,
            "wire_bottom": 28,
            "total_cost": "",
            "useful_length": "",
            "useful_cost": "",
            "free_length": "",
            "free_cost": "",
            "orders": [
              {
                "number": "Т6",
                "plates": [
                  {
                    "count": 1,
                    "length": 5200,
                    "production_plate": {
                      "material_cost": ""
                    },
                    "order_plate": {
                      "material_cost": "",
                      "concrete_class": "B25",
                      "wire_top": 4,
                      "wire_bottom": 12
                    }
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### status code `422`:

```json
{
  "detail": [
    {
      "loc": [
        "string",
        0
      ],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

PS: Ошибка валидации(передали неверные типы данных)

2. POST - `/api/v1/calculate/no-limits`

Оптимизация календарного плана, без ограничений на количество дорожек и без ограничения на дату готовности

### Все тоже самое что и в первом запросе, отличается только внутренняя логика