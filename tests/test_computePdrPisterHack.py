#
# import pytest
# import random
# import Wireless
#
# # ============================ fixtures ==============================
#
# EXPECTEDINOUT = [
#
#     # two close positions ( <1 m apart)
#     {
#         'in': {
#             'sender_pos':     (0.00, 0.00),
#             'receiver_pos':   (0.00, 0.50),
#         },
#
#         'out': 1.00
#     },
#
#     # two out of range positions (1000 m)
#     {
#         'in': {
#             'sender_pos':   (   0.00,    0.00),
#             'receiver_pos': (   0.00, 1000.00),
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
#     'sender_pos':   (random.uniform(0.00, 1000.00), random.uniform(0.00, 1000.00)),
#     'receiver_pos': (random.uniform(0.00, 1000.00), random.uniform(0.00, 1000.00)),
#     }
#     for i in range(1000)
# ]
#
# @pytest.fixture(params=RANDOMPOSITIONS)
# def randomPositions(request):
#     return request.param
#
# # ============================ tests =================================
#
# def test_computePdrPisterHack(expectedInOut):
#     '''
#     testing PDR computation based on set distances
#     '''
#
#     wireless = Wireless.Wireless()
#
#     assert wireless._computePdrPisterHack(*expectedInOut['in'].values()) == expectedInOut['out']
#
# def test_computePdrPisterHackRandom(randomPositions):
#     '''
#     testing PDR computation based on random distances
#     '''
#
#     wireless = Wireless.Wireless()
#
#     assert 0 <= wireless._computePdrPisterHack(*randomPositions.values()) <= 1

