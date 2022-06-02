#
# import pytest
# import random
# import Wireless
# import DotBot
#
# # ============================ fixtures ==============================
#
# EXPECTEDINOUT = [
#
#     # two close positions ( <1 m apart)
#     {
#         'in': {
#             'sender':     DotBot.DotBot(dotBotId=1,x=0.00, y=0.00,floorplan='#'),
#             'receiver':   DotBot.DotBot(dotBotId=1,x=0.00, y=0.50,floorplan='#')
#         },
#
#         'out': 1.00
#     },
#
#     # two out of range positions (1000 m)
#     {
#         'in': {
#             'sender':   DotBot.DotBot(dotBotId=1,x=0.00, y=0.00,floorplan='#'),
#             'receiver': DotBot.DotBot(dotBotId=1,x=0.00, y=1000.00,floorplan='#'),
#         },
#
#         'out': 0.00
#     },
# ]
#
# @pytest.fixture(params=EXPECTEDINOUT)
# def expectedInOut(request):
#     return request.param
#
# RANDOMPOSITIONS = [{
#     'sender':   DotBot.DotBot(dotBotId=1,x=random.uniform(0.00, 1000.00), y=random.uniform(0.00, 1000.00),floorplan='#'),
#     'receiver': DotBot.DotBot(dotBotId=1,x=random.uniform(0.00, 1000.00), y=random.uniform(0.00, 1000.00),floorplan='#'),
#     }
#     for i in range(1000)
# ]
#
# @pytest.fixture(params=RANDOMPOSITIONS)
# def randomPositions(request):
#     return request.param
#
# #============================ tests =================================
#
# # def test_computePdrPisterHack(expectedInOut):
# #     '''
# #     testing PDR computation based on set distances
# #     '''
# #
# #     wireless = Wireless.Wireless()
# #
# #     assert wireless._computePdrPisterHack(*expectedInOut['in'].values()) == expectedInOut['out']
#
#
# def test_computePdrPisterHackRandom(randomPositions):
#     '''
#     testing PDR computation based on random distances
#     '''
#
#     wireless = Wireless.Wireless()
#
#     # friis pdr
#     wireless.PISTER_HACK_LOWER_SHIFT = 0
#     pdr_friis = wireless._computePdrPisterHack(*randomPositions.values())
#
#     # pister hack pdr
#     wireless.PISTER_HACK_LOWER_SHIFT = 40
#     pdr_pisterHack = wireless._computePdrPisterHack(*randomPositions.values())
#
#     assert 0 <= pdr_pisterHack <= 1
#     assert pdr_pisterHack <= pdr_friis

