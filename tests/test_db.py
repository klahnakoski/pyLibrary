# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals
from __future__ import division

import re
import unittest
from pyLibrary import convert
from pyLibrary.queries.db_query import esfilter2sqlwhere
from pyLibrary.sql import db
from pyLibrary.sql.db import DB
from pyLibrary.debugs.logs import Log
from pyLibrary.dot.nones import Null

__author__ = 'klahnakoski'

class TestDB(unittest.TestCase):
    def test_int_packer(self):
        v = [801000, 801001, 801002, 801003, 801004, 801005, 801006, 801007, 801008, 801009, 801010, 801011, 801012, 801013, 801014, 801015, 801016, 801017, 801018, 801019, 801020, 801021, 801022, 801023,
             801024, 801025, 801026, 801028, 801029, 801030, 801032, 801034, 801035, 801036, 801037, 801038, 801040, 801042, 801043, 801044, 801045, 801047, 801048, 801049, 801050, 801051, 801052, 801053,
             801055, 801056, 801057, 801058, 801059, 801060, 801061, 801062, 801063, 801065, 801066, 801067, 801068, 801069, 801070, 801071, 801072, 801073, 801074, 801075, 801076, 801077, 801078, 801079,
             801080, 801081, 801083, 801084, 801085, 801086, 801087, 801088, 801089, 801090, 801091, 801092, 801093, 801094, 801095, 801096, 801097, 801098, 801099, 801100, 801101, 801102, 801103, 801104,
             801105, 801106, 801107, 801108, 801109, 801110, 801111, 801112, 801113, 801116, 801117, 801118, 801119, 801120, 801121, 801122, 801123, 801124, 801125, 801126, 801128, 801129, 801130, 801131,
             801132, 801133, 801134, 801135, 801136, 801137, 801138, 801139, 801140, 801141, 801142, 801143, 801144, 801145, 801146, 801147, 801148, 801149, 801150, 801151, 801152, 801153, 801154, 801155,
             801156, 801158, 801159, 801160, 801161, 801162, 801163, 801164, 801165, 801166, 801167, 801168, 801169, 801170, 801171, 801172, 801173, 801174, 801175, 801176, 801177, 801178, 801179, 801180,
             801181, 801182, 801183, 801184, 801185, 801186, 801187, 801188, 801189, 801190, 801191, 801192, 801193, 801194, 801196, 801197, 801198, 801199, 801200, 801201, 801202, 801203, 801204, 801205,
             801207, 801208, 801209, 801210, 801211, 801212, 801213, 801214, 801215, 801216, 801217, 801218, 801219, 801222, 801223, 801224, 801225, 801226, 801229, 801230, 801231, 801232, 801233, 801235,
             801236, 801237, 801238, 801239, 801240, 801241, 801242, 801243, 801244, 801245, 801246, 801247, 801253, 801254, 801255, 801256, 801257, 801258, 801260, 801261, 801262, 801263, 801264, 801265,
             801266, 801267, 801268, 801269, 801270, 801271, 801272, 801273, 801274, 801275, 801276, 801277, 801278, 801279, 801280, 801281, 801282, 801283, 801284, 801285, 801286, 801287, 801288, 801289,
             801290, 801291, 801292, 801293, 801294, 801295, 801296, 801297, 801298, 801300, 801301, 801303, 801304, 801305, 801306, 801307, 801308, 801309, 801310, 801311, 801312, 801313, 801314, 801315,
             801316, 801317, 801318, 801319, 801320, 801321, 801322, 801323, 801324, 801325, 801326, 801327, 801328, 801329, 801331, 801332, 801333, 801334, 801336, 801337, 801338, 801339, 801340, 801341,
             801343, 801344, 801345, 801346, 801347, 801348, 801349, 801350, 801351, 801352, 801353, 801354, 801355, 801356, 801357, 801358, 801359, 801360, 801361, 801362, 801363, 801364, 801365, 801367,
             801368, 801369, 801370, 801371, 801372, 801373, 801374, 801375, 801376, 801377, 801378, 801379, 801380, 801381, 801382, 801383, 801384, 801385, 801386, 801387, 801388, 801389, 801390, 801391,
             801393, 801394, 801395, 801396, 801397, 801398, 801399, 801400, 801401, 801402, 801403, 801404, 801405, 801406, 801407, 801408, 801409, 801410, 801411, 801412, 801413, 801414, 801415, 801416,
             801417, 801418, 801419, 801420, 801421, 801422, 801423, 801424, 801425, 801426, 801427, 801428, 801429, 801430, 801431, 801432, 801433, 801434, 801435, 801436, 801437, 801439, 801440, 801441,
             801442, 801443, 801444, 801445, 801446, 801447, 801448, 801449, 801450, 801451, 801452, 801453, 801454, 801455, 801456, 801457, 801458, 801459, 801460, 801461, 801462, 801463, 801464, 801465,
             801466, 801467, 801468, 801469, 801470, 801471, 801472, 801473, 801474, 801475, 801476, 801477, 801478, 801479, 801480, 801481, 801482, 801483, 801484, 801485, 801486, 801487, 801488, 801489,
             801490, 801491, 801492, 801493, 801494, 801495, 801496, 801497, 801498, 801499, 801500, 801501, 801502, 801503, 801505, 801506, 801507, 801508, 801509, 801510, 801511, 801512, 801513, 801514,
             801515, 801516, 801517, 801518, 801519, 801520, 801521, 801522, 801523, 801524, 801525, 801526, 801527, 801528, 801529, 801530, 801531, 801532, 801533, 801534, 801535, 801536, 801537, 801538,
             801539, 801540, 801541, 801542, 801543, 801544, 801545, 801546, 801547, 801548, 801549, 801550, 801551, 801552, 801553, 801554, 801555, 801556, 801557, 801558, 801559, 801560, 801561, 801562,
             801563, 801564, 801565, 801566, 801567, 801568, 801569, 801571, 801572, 801573, 801574, 801575, 801576, 801577, 801578, 801579, 801580, 801581, 801582, 801583, 801584, 801585, 801587, 801589,
             801590, 801591, 801592, 801593, 801595, 801596, 801597, 801598, 801599, 801600, 801601, 801602, 801603, 801604, 801605, 801606, 801607, 801608, 801609, 801610, 801611, 801612, 801613, 801614,
             801615, 801616, 801617, 801618, 801619, 801620, 801621, 801622, 801623, 801624, 801625, 801626, 801627, 801628, 801629, 801630, 801631, 801632, 801633, 801634, 801635, 801636, 801637, 801639,
             801640, 801642, 801643, 801644, 801645, 801646, 801647, 801649, 801650, 801651, 801652, 801653, 801655, 801656, 801658, 801659, 801660, 801661, 801662, 801663, 801664, 801665, 801666, 801667,
             801668, 801669, 801670, 801671, 801672, 801674, 801675, 801676, 801677, 801678, 801679, 801680, 801681, 801682, 801683, 801684, 801685, 801686, 801687, 801688, 801690, 801691, 801693, 801694,
             801695, 801696, 801697, 801698, 801699, 801701, 801702, 801703, 801705, 801706, 801707, 801708, 801710, 801711, 801712, 801713, 801714, 801715, 801716, 801717, 801718, 801719, 801720, 801721,
             801722, 801723, 801724, 801725, 801726, 801727, 801729, 801730, 801731, 801732, 801733, 801734, 801737, 801738, 801739, 801740, 801741, 801742, 801743, 801744, 801745, 801747, 801748, 801749,
             801750, 801752, 801753, 801754, 801755, 801756, 801757, 801758, 801759, 801760, 801761, 801763, 801764, 801765, 801766, 801767, 801769, 801771, 801773, 801774, 801775, 801776, 801778, 801779,
             801780, 801781, 801782, 801783, 801784, 801785, 801786, 801787, 801788, 801789, 801791, 801792, 801793, 801794, 801795, 801796, 801797, 801798, 801799, 801800, 801801, 801802, 801803, 801804,
             801805, 801806, 801807, 801808, 801809, 801810, 801811, 801812, 801813, 801814, 801816, 801817, 801818, 801819, 801820, 801821, 801823, 801824, 801825, 801826, 801827, 801828, 801829, 801830,
             801832, 801833, 801834, 801835, 801836, 801837, 801838, 801839, 801840, 801841, 801842, 801843, 801844, 801845, 801846, 801847, 801849, 801850, 801852, 801855, 801856, 801857, 801858, 801859,
             801860, 801862, 801869, 801872, 801874, 801880, 801882, 801883, 801884, 801885, 801891, 801892, 801895, 801897, 801898, 801899, 801902, 801905, 801906, 801909, 801911, 801912, 801913, 801914,
             801915, 801916, 801917, 801918, 801919, 801920, 801921, 801922, 801923, 801924, 801925, 801926, 801927, 801928, 801929, 801930, 801931, 801932, 801934, 801935, 801936, 801937, 801938, 801941,
             801942, 801943, 801944, 801945, 801946, 801947, 801948, 801949, 801950, 801951, 801952, 801953, 801954, 801955, 801956, 801957, 801958, 801960, 801961, 801962, 801964, 801965, 801966, 801967,
             801969, 801970, 801971, 801972, 801973, 801974, 801976, 801977, 801978, 801979, 801980, 801981, 801982, 801983, 801984, 801985, 801986, 801987, 801988, 801989, 801990, 801991, 801993, 801994,
             801995, 801996, 801998]

        int_list = convert.value2intlist(v)
        result = db.int_list_packer("bug_id", int_list)
        json = convert.value2json(result)
        reference = '{"or": [{"terms": {"bug_id": [801869, 801872, 801874, 801880, 801882, 801883, 801884, 801885, 801891, 801892, 801895, 801897, 801898, 801899, 801902, 801905, 801906, 801909, 801911, 801912, 801913, 801914, 801915, 801916, 801917, 801918, 801919, 801920, 801921, 801922, 801923, 801924, 801925, 801926, 801927, 801928, 801929, 801930, 801931, 801932, 801934, 801935, 801936, 801937, 801938, 801941, 801942, 801943, 801944, 801945, 801946, 801947, 801948, 801949, 801950, 801951, 801952, 801953, 801954, 801955, 801956, 801957, 801958, 801960, 801961, 801962, 801964, 801965, 801966, 801967, 801969, 801970, 801971, 801972, 801973, 801974, 801976, 801977, 801978, 801979, 801980, 801981, 801982, 801983, 801984, 801985, 801986, 801987, 801988, 801989, 801990, 801991, 801993, 801994, 801995, 801996, 801998]}}, {"and": [{"or": [{"range": {"bug_id": {"gte": 801000, "lte": 801045}}}, {"range": {"bug_id": {"gte": 801047, "lte": 801247}}}, {"range": {"bug_id": {"gte": 801253, "lte": 801862}}}]}, {"not": {"terms": {"bug_id": [801027, 801031, 801033, 801039, 801041, 801054, 801064, 801082, 801114, 801115, 801127, 801157, 801195, 801206, 801220, 801221, 801227, 801228, 801234, 801259, 801299, 801302, 801330, 801335, 801342, 801366, 801392, 801438, 801504, 801570, 801586, 801588, 801594, 801638, 801641, 801648, 801654, 801657, 801673, 801689, 801692, 801700, 801704, 801709, 801728, 801735, 801736, 801746, 801751, 801762, 801768, 801770, 801772, 801777, 801790, 801815, 801822, 801831, 801848, 801851, 801853, 801854, 801861]}}}]}]}'


        if json != reference:
            Log.note("json={{json}}", {"json": json})
            Log.error("Error")

    def test_filter2where(self):
        v = [856000, 856001, 856002, 856003, 856004, 856006, 856007, 856008, 856009, 856011, 856012, 856013, 856014, 856015, 856016, 856017, 856018, 856020, 856021, 856022, 856023, 856024, 856025, 856026,
             856027, 856028, 856030, 856031, 856032, 856034, 856037, 856038, 856039, 856040, 856041, 856043, 856045, 856047, 856048, 856049, 856050, 856051, 856052, 856053, 856054, 856055, 856056, 856058,
             856059, 856062, 856070, 856071, 856072, 856073, 856074, 856075, 856076, 856077, 856078, 856079, 856080, 856081, 856082, 856083, 856084, 856085, 856086, 856087, 856088, 856089, 856090, 856092,
             856093, 856094, 856095, 856096, 856097, 856098, 856100, 856101, 856102, 856103, 856105, 856107, 856108, 856109, 856110, 856111, 856112, 856113, 856114, 856115, 856116, 856117, 856118, 856119,
             856120, 856121, 856122, 856123, 856124, 856127, 856128, 856129, 856130, 856131, 856132, 856133, 856134, 856137, 856138, 856139, 856140, 856141, 856142, 856143, 856144, 856145, 856146, 856147,
             856148, 856149, 856150, 856151, 856152, 856153, 856154, 856155, 856156, 856158, 856159, 856160, 856163, 856165, 856166, 856167, 856168, 856169, 856170, 856171, 856172, 856176, 856177, 856178,
             856179, 856180, 856182, 856183, 856184, 856186, 856187, 856188, 856189, 856190, 856191, 856192, 856193, 856194, 856195, 856196, 856197, 856198, 856199, 856201, 856202, 856203, 856204, 856205,
             856206, 856207, 856208, 856209, 856210, 856211, 856212, 856213, 856214, 856215, 856216, 856217, 856222, 856223, 856224, 856225, 856226, 856227, 856228, 856229, 856230, 856232, 856233, 856234,
             856235, 856238, 856239, 856240, 856241, 856242, 856244, 856245, 856246, 856247, 856248, 856249, 856250, 856251, 856252, 856253, 856254, 856255, 856256, 856257, 856258, 856260, 856261, 856262,
             856263, 856264, 856265, 856266, 856267, 856268, 856269, 856270, 856272, 856273, 856275, 856276, 856277, 856278, 856279, 856280, 856281, 856282, 856283, 856284, 856285, 856286, 856287, 856288,
             856289, 856290, 856291, 856292, 856295, 856296, 856297, 856298, 856299, 856300, 856301, 856302, 856303, 856304, 856305, 856306, 856307, 856308, 856309, 856310, 856311, 856312, 856313, 856314,
             856315, 856316, 856317, 856318, 856319, 856321, 856322, 856323, 856324, 856325, 856327, 856328, 856329, 856330, 856331, 856332, 856333, 856335, 856337, 856338, 856339, 856340, 856341, 856342,
             856344, 856345, 856346, 856349, 856350, 856351, 856352, 856353, 856354, 856355, 856356, 856357, 856358, 856359, 856360, 856361, 856362, 856363, 856364, 856365, 856366, 856367, 856368, 856369,
             856370, 856371, 856372, 856373, 856375, 856378, 856381, 856383, 856385, 856386, 856387, 856388, 856389, 856390, 856391, 856392, 856393, 856394, 856396, 856397, 856400, 856401, 856402, 856403,
             856404, 856405, 856406, 856407, 856408, 856409, 856410, 856411, 856412, 856413, 856414, 856415, 856417, 856418, 856419, 856420, 856421, 856422, 856423, 856424, 856425, 856426, 856427, 856429,
             856430, 856431, 856432, 856433, 856434, 856436, 856437, 856438, 856439, 856440, 856441, 856442, 856443, 856444, 856445, 856448, 856450, 856451, 856452, 856453, 856454, 856455, 856456, 856457,
             856458, 856459, 856460, 856461, 856462, 856463, 856464, 856465, 856466, 856467, 856468, 856469, 856470, 856471, 856472, 856474, 856475, 856476, 856477, 856478, 856479, 856481, 856482, 856484,
             856485, 856486, 856487, 856489, 856490, 856491, 856492, 856493, 856494, 856495, 856496, 856497, 856498, 856499, 856500, 856501, 856502, 856503, 856504, 856505, 856506, 856507, 856508, 856509,
             856511, 856512, 856513, 856514, 856515, 856516, 856517, 856518, 856519, 856520, 856521, 856522, 856523, 856524, 856525, 856526, 856527, 856528, 856529, 856530, 856531, 856532, 856533, 856534,
             856535, 856536, 856538, 856540, 856541, 856542, 856543, 856544, 856545, 856546, 856547, 856548, 856549, 856550, 856551, 856552, 856553, 856554, 856555, 856556, 856557, 856558, 856559, 856560,
             856561, 856562, 856565, 856566, 856567, 856568, 856569, 856571, 856572, 856574, 856575, 856576, 856577, 856579, 856580, 856581, 856582, 856583, 856584, 856585, 856586, 856587, 856588, 856590,
             856591, 856592, 856593, 856594, 856595, 856596, 856598, 856599, 856600, 856601, 856602, 856603, 856604, 856605, 856606, 856607, 856608, 856609, 856611, 856612, 856613, 856614, 856615, 856616,
             856617, 856618, 856619, 856620, 856621, 856622, 856623, 856624, 856625, 856626, 856627, 856629, 856630, 856631, 856632, 856633, 856634, 856635, 856637, 856638, 856639, 856640, 856641, 856642,
             856643, 856644, 856645, 856646, 856647, 856651, 856653, 856654, 856657, 856658, 856659, 856660, 856661, 856662, 856664, 856665, 856666, 856670, 856671, 856672, 856673, 856674, 856675, 856676,
             856677, 856678, 856679, 856680, 856681, 856682, 856683, 856684, 856685, 856687, 856688, 856689, 856690, 856691, 856692, 856693, 856694, 856695, 856696, 856697, 856698, 856699, 856700, 856701,
             856702, 856703, 856705, 856707, 856708, 856709, 856710, 856711, 856712, 856713, 856715, 856716, 856717, 856718, 856720, 856728, 856729, 856731, 856732, 856733, 856734, 856736, 856738, 856739,
             856740, 856741, 856742, 856743]

        where = esfilter2sqlwhere(DB(Null), {"terms": {"bug_id": v}})
        reference = """
        (
            `bug_id` in (856000, 856001, 856002, 856003, 856004, 856006, 856007, 856008, 856009, 856011, 856012, 856013, 856014, 856015, 856016, 856017, 856018, 856020, 856021, 856022, 856023, 856024, 856025, 856026, 856027, 856028, 856030, 856031, 856032, 856034, 856037, 856038, 856039, 856040, 856041, 856043, 856045, 856047, 856048, 856049, 856050, 856051, 856052, 856053, 856054, 856055, 856056, 856058, 856059, 856062, 856165, 856166, 856167, 856168, 856169, 856170, 856171, 856172, 856176, 856177, 856178, 856179, 856180, 856182, 856183, 856184, 856222, 856223, 856224, 856225, 856226, 856227, 856228, 856229, 856230, 856232, 856233, 856234, 856235, 856238, 856239, 856240, 856241, 856242, 856381, 856383, 856651, 856653, 856654, 856657, 856658, 856659, 856660, 856661, 856662, 856664, 856665, 856666, 856728, 856729, 856731, 856732, 856733, 856734, 856736, 856738, 856739, 856740, 856741, 856742, 856743) OR
            (
                (
                    `bug_id` BETWEEN 856070 AND 856163 OR
                    `bug_id` BETWEEN 856186 AND 856217 OR
                    `bug_id` BETWEEN 856244 AND 856378 OR
                    `bug_id` BETWEEN 856385 AND 856448 OR
                    `bug_id` BETWEEN 856450 AND 856647 OR
                    `bug_id` BETWEEN 856670 AND 856720
                ) AND
                NOT (`bug_id` in (856091, 856099, 856104, 856106, 856125, 856126, 856135, 856136, 856157, 856161, 856162, 856200, 856259, 856271, 856274, 856293, 856294, 856320, 856326, 856334, 856336, 856343, 856347, 856348, 856374, 856376, 856377, 856395, 856398, 856399, 856416, 856428, 856435, 856446, 856447, 856473, 856480, 856483, 856488, 856510, 856537, 856539, 856563, 856564, 856570, 856573, 856578, 856589, 856597, 856610, 856628, 856636, 856686, 856704, 856706, 856714, 856719))
            )
        )"""
        reference = re.sub(r"\s+", " ", reference).strip()
        where = re.sub(r"\s+", " ", where).strip()

        if where != reference:
            Log.note(where)
            Log.error("error")


