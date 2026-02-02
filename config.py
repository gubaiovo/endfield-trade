# config.py
# -*- coding: utf-8 -*-

GAME_WINDOW_TITLE = "Endfield"
MATCH_THRESHOLD = 0.85
LOG = True

TITLE_BAR_HEIGHT = 45
BORDER_WIDTH = 8

REGION_DATA = {
    "四号谷地": {
        "count": 12,
        "marker": "gudi_diaodujuan.jpg",
        "y_filter": 300,
    },
    "武陵": {
        "count": 4,
        "marker": "wuling_diaodujuan.jpg",
        "y_filter": 300,
    },
}

# 识别区域 (x, y, w, h)
AREA_ITEM_NAME = (730, 320, 250, 40)
AREA_MY_PRICE = (1535, 410, 75, 30)
AREA_MARKET_PRICE = (1205, 490, 65, 30)

# 按钮坐标 (x, y)
BTN_SWITCH_MARKET_X = 1500
BTN_SWITCH_MARKET_Y = 730

BTN_CLOSE_X = 1630
BTN_CLOSE_Y = 262

# 备用默认值
DEFAULT_COUNT = 14