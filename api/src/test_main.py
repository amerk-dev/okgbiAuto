from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_calculate_plate():
    response = client.post(
        "/api/v1/calculate/",
        json={
            "directory": {
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
                "track": {
                    "length": 85000
                }
            },
            "ready_plates": [
                {
                    "count": 5,
                    "length": 2800,
                    "width": 1000,
                    "height": 220,
                    "class": "B25",
                    "wire_bottom": 4,
                    "wire_top": 4
                },
                {
                    "count": 3,
                    "length": 3200,
                    "width": 1200,
                    "height": 240,
                    "class": "B30",
                    "wire_bottom": 6,
                    "wire_top": 6
                }
            ],
            "available_tracks": [
                {
                    "count": 2,
                    "day": "2025-03-18"
                },
                {
                    "count": 3,
                    "day": "2025-03-19"
                }
            ],
            "orders": [
                {
                    "number": "Т6",
                    "production_days": 2,
                    "completion_dates": [
                        {
                            "date": "2025-03-18",
                            "plates": [
                                {
                                    "count": 2,
                                    "length": 2800,
                                    "width": 1000,
                                    "height": 220,
                                    "class": "B25",
                                    "wire_bottom": 4,
                                    "wire_top": 4
                                }
                            ]
                        },
                        {
                            "date": "2025-03-19",
                            "plates": [
                                {
                                    "count": 1,
                                    "length": 3200,
                                    "width": 1200,
                                    "height": 240,
                                    "class": "B30",
                                    "wire_bottom": 6,
                                    "wire_top": 6
                                }
                            ]
                        }
                    ]
                },
                {
                    "number": "Т7",
                    "production_days": 1,
                    "completion_dates": [
                        {
                            "date": "2025-03-19",
                            "plates": [
                                {
                                    "count": 3,
                                    "length": 2800,
                                    "width": 1000,
                                    "height": 220,
                                    "class": "B25",
                                    "wire_bottom": 4,
                                    "wire_top": 4
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "number": "Т6",
            "production_days": 2,
            "completion_dates": [
                {
                    "date": "2025-03-18",
                    "plates": [
                        {
                            "count": 2,
                            "length": 2800,
                            "width": 1000,
                            "height": 220,
                            "class": "B25",
                            "wire_bottom": 4,
                            "wire_top": 4
                        }
                    ]
                },
                {
                    "date": "2025-03-19",
                    "plates": [
                        {
                            "count": 1,
                            "length": 3200,
                            "width": 1200,
                            "height": 240,
                            "class": "B30",
                            "wire_bottom": 6,
                            "wire_top": 6
                        }
                    ]
                }
            ]
        },
        {
            "number": "Т7",
            "production_days": 1,
            "completion_dates": [
                {
                    "date": "2025-03-19",
                    "plates": [
                        {
                            "count": 3,
                            "length": 2800,
                            "width": 1000,
                            "height": 220,
                            "class": "B25",
                            "wire_bottom": 4,
                            "wire_top": 4
                        }
                    ]
                }
            ]
        }
    ]
