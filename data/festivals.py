FESTIVAL_MULTIPLIERS = {
    "Diwali": 15,
    "Navratri": 12,
    "Dussehra": 10,
    "Pongal": 8,
    "Tamil New Year": 6,
    "Holi": 9,
    "Ganesh Chaturthi": 11,
    "Karthigai Deepam": 7,
    "Aadi Perukku": 5,
    "Vaikunta Ekadasi": 8,
    "Shivaratri": 9,
    "Rama Navami": 6,
    "Krishna Jayanthi": 7,
    "Skanda Sashti": 6,
    "Ayyappa Pooja": 5,
    "Normal Weekday": 1,
    "Normal Weekend": 2,
    "Monthly Festival": 3,
}

# Sample training data: [temple_size(1-3), day_type(1-5), festival_multiplier] -> kg_waste
TRAINING_DATA = [
    # small temple
    [1, 1, 1, 15], [1, 2, 2, 28], [1, 3, 6, 85], [1, 3, 8, 110],
    [1, 3, 9, 120], [1, 3, 10, 135], [1, 3, 11, 150], [1, 3, 12, 160],
    [1, 3, 15, 200],
    # medium temple
    [2, 1, 1, 40], [2, 2, 2, 75], [2, 3, 6, 220], [2, 3, 8, 290],
    [2, 3, 9, 310], [2, 3, 10, 350], [2, 3, 11, 400], [2, 3, 12, 430],
    [2, 3, 15, 550],
    # large temple
    [3, 1, 1, 80], [3, 2, 2, 150], [3, 3, 6, 450], [3, 3, 8, 580],
    [3, 3, 9, 620], [3, 3, 10, 700], [3, 3, 11, 800], [3, 3, 12, 860],
    [3, 3, 15, 1100],
]
