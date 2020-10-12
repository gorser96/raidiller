from enum import Enum, IntEnum


class RaidScreen(Enum):
    MAIN_MENU = 1
    ACTIONS = 2
    CAMPAIGN = 3
    DUNGEON = 4
    WAR_OF_FRACTIONS = 5
    ARENA = 6
    CLAN_BOSS = 7
    FATAL_TOWER = 8
    CAMPAIGN_LEVEL = 9
    PRE_FIGHT = 10
    FIGHT = 11


class CampaignDifficult(IntEnum):
    SIMPLE = 1
    HARD = 2
    IMPOSSIBLE = 3
    HELL = 4
