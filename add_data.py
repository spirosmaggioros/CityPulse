import asyncio
import os

import dotenv
import httpx

dotenv.load_dotenv()


_http_client = httpx.AsyncClient(
    base_url="https://citypulse.freeddns.us/api",
    timeout=30,
    limits=httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
        keepalive_expiry=60,
    ),
)


locations = [
    {
        "location": "Ano Liosia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6987, 38.0823]},
    },
    {
        "location": "Agia Paraskevi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8194, 37.9987]},
    },
    {
        "location": "Cholargos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7985, 37.9895]},
    },
    {
        "location": "Zografou, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7598, 37.9712]},
    },
    {
        "location": "Dafni, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7487, 37.9523]},
    },
    {
        "location": "Ilioupoli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7667, 37.9301]},
    },
    {
        "location": "Alimos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7230, 37.9108]},
    },
    {
        "location": "Nea Smyrni, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7151, 37.9463]},
    },
    {
        "location": "Kallithea, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7024, 37.9557]},
    },
    {
        "location": "Peristeri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6882, 38.0142]},
    },
    {
        "location": "Petroupoli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6753, 38.0317]},
    },
    {
        "location": "Ilion, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6981, 38.0297]},
    },
    {
        "location": "Acharnes, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7322, 38.0832]},
    },
    {
        "location": "Maroussi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7999, 38.0565]},
    },
    {
        "location": "Vrilissia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8315, 38.0382]},
    },
    {
        "location": "Pallini, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8762, 38.0012]},
    },
    {
        "location": "Koropi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8766, 37.9012]},
    },
    {
        "location": "Stavros, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8614, 37.9887]},
    },
    {
        "location": "Keratsini, Piraeus",
        "coordinates": {"type": "Point", "coordinates": [23.6232, 37.9621]},
    },
    {
        "location": "Nikaia, Piraeus",
        "coordinates": {"type": "Point", "coordinates": [23.6468, 37.9671]},
    },
    {
        "location": "Evosmos, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.8964, 40.6627]},
    },
    {
        "location": "Stavroupoli, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9143, 40.6724]},
    },
    {
        "location": "Ampelokipoi, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9677, 40.6418]},
    },
    {
        "location": "Thermi, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [23.0189, 40.5456]},
    },
    {
        "location": "Oraiokastro, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9178, 40.7268]},
    },
    {
        "location": "Neapoli, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9731, 40.6534]},
    },
    {
        "location": "Komotini",
        "coordinates": {"type": "Point", "coordinates": [25.4018, 41.1220]},
    },
    {
        "location": "Serres",
        "coordinates": {"type": "Point", "coordinates": [23.5481, 41.0847]},
    },
    {
        "location": "Veria",
        "coordinates": {"type": "Point", "coordinates": [22.2033, 40.5233]},
    },
    {
        "location": "Larissa",
        "coordinates": {"type": "Point", "coordinates": [22.4191, 39.6390]},
    },
    {
        "location": "Trikala",
        "coordinates": {"type": "Point", "coordinates": [21.7681, 39.5559]},
    },
    {
        "location": "Lamia",
        "coordinates": {"type": "Point", "coordinates": [22.4344, 38.8981]},
    },
    {
        "location": "Agrinio",
        "coordinates": {"type": "Point", "coordinates": [21.4083, 38.6215]},
    },
    {
        "location": "Pyrgos, Elis",
        "coordinates": {"type": "Point", "coordinates": [21.4397, 37.6756]},
    },
    {
        "location": "Kalamata",
        "coordinates": {"type": "Point", "coordinates": [22.1142, 37.0389]},
    },
    {
        "location": "Sparti",
        "coordinates": {"type": "Point", "coordinates": [22.4295, 37.0737]},
    },
    {
        "location": "Argos",
        "coordinates": {"type": "Point", "coordinates": [22.7222, 37.6333]},
    },
    {
        "location": "Kozani",
        "coordinates": {"type": "Point", "coordinates": [21.7892, 40.3006]},
    },
    {
        "location": "Florina",
        "coordinates": {"type": "Point", "coordinates": [21.4072, 40.7803]},
    },
    {
        "location": "Kastoria",
        "coordinates": {"type": "Point", "coordinates": [21.2694, 40.5192]},
    },
    {
        "location": "Grevena",
        "coordinates": {"type": "Point", "coordinates": [21.4267, 40.0844]},
    },
    {
        "location": "Karditsa",
        "coordinates": {"type": "Point", "coordinates": [21.9217, 39.3653]},
    },
    {
        "location": "Preveza",
        "coordinates": {"type": "Point", "coordinates": [20.7514, 38.9557]},
    },
    {
        "location": "Lefkada Town",
        "coordinates": {"type": "Point", "coordinates": [20.7054, 38.8332]},
    },
    {
        "location": "Pylos, Messenia",
        "coordinates": {"type": "Point", "coordinates": [21.6956, 36.9138]},
    },
    {
        "location": "Leoforos Kifisias 120, Ampelokipoi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7712, 37.9891]},
    },
    {
        "location": "Leoforos Vouliagmenis 85, Argyroupoli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7523, 37.9201]},
    },
    {
        "location": "Iera Odos 45, Egaleo, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6821, 37.9987]},
    },
    {
        "location": "Leoforos Athinon 210, Peristeri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6901, 38.0198]},
    },
    {
        "location": "Liosion 78, Kato Patisia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7312, 38.0021]},
    },
    {
        "location": "Alexandras 132, Ampelokipoi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7498, 37.9923]},
    },
    {
        "location": "Nimfeon 12, Galatsi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7401, 38.0198]},
    },
    {
        "location": "Patision 201, Ano Patisia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7354, 38.0087]},
    },
    {
        "location": "Syngrou 95, Neos Kosmos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7298, 37.9612]},
    },
    {
        "location": "Pireos 180, Tavros, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7089, 37.9712]},
    },
    {
        "location": "Ethnikis Antistaseos 34, Chalandri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8021, 38.0201]},
    },
    {
        "location": "Mesogeion 256, Holargos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8012, 37.9934]},
    },
    {
        "location": "Davelis 5, Penteli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8654, 38.0534]},
    },
    {
        "location": "Thermopylon 17, Nea Ionia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7598, 38.0356]},
    },
    {
        "location": "Kyprou 43, Metamorfosi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7632, 38.0634]},
    },
    {
        "location": "Chalandri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8021, 38.0201]},
    },
    {
        "location": "Galatsi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7401, 38.0198]},
    },
    {
        "location": "Nea Ionia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7598, 38.0356]},
    },
    {
        "location": "Metamorfosi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7632, 38.0634]},
    },
    {
        "location": "Kifisia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8107, 38.0737]},
    },
    {
        "location": "Ekali, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8223, 38.1031]},
    },
    {
        "location": "Nea Erythraia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8101, 38.0921]},
    },
    {
        "location": "Lykovrysi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7812, 38.0712]},
    },
    {
        "location": "Pefki, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7901, 38.0634]},
    },
    {
        "location": "Irakleio, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7701, 38.0534]},
    },
    {
        "location": "Nea Filadelfia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7512, 38.0456]},
    },
    {
        "location": "Nea Chalkidona, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7423, 38.0398]},
    },
    {
        "location": "Moschato, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6987, 37.9534]},
    },
    {
        "location": "Tavros, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7089, 37.9712]},
    },
    {
        "location": "Egaleo, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6821, 37.9987]},
    },
    {
        "location": "Korydallos, Piraeus",
        "coordinates": {"type": "Point", "coordinates": [23.6568, 37.9823]},
    },
    {
        "location": "Agios Ioannis Rentis, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6923, 37.9634]},
    },
    {
        "location": "Vyronas, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7712, 37.9634]},
    },
    {
        "location": "Kaisariani, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7612, 37.9701]},
    },
    {
        "location": "Papagou, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8012, 37.9878]},
    },
    {
        "location": "Glyfada, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7523, 37.8801]},
    },
    {
        "location": "Argyroupoli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7523, 37.9201]},
    },
    {
        "location": "Elliniko, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7323, 37.8923]},
    },
    {
        "location": "Voula, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7634, 37.8501]},
    },
    {
        "location": "Vouliagmeni, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7812, 37.8101]},
    },
    {
        "location": "Vari, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8012, 37.8312]},
    },
    {
        "location": "Agios Dimitrios, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7312, 37.9423]},
    },
    {
        "location": "Penteli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8654, 38.0534]},
    },
    {
        "location": "Gerakas, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8723, 38.0212]},
    },
    {
        "location": "Anthousa, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8834, 38.0101]},
    },
    {
        "location": "Paiania, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8634, 37.9534]},
    },
    {
        "location": "Spata, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.9123, 37.9612]},
    },
    {
        "location": "Artemida, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.9423, 37.9823]},
    },
    {
        "location": "Rafina, Athens",
        "coordinates": {"type": "Point", "coordinates": [24.0023, 38.0234]},
    },
    {
        "location": "Marathonas, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.9712, 38.1534]},
    },
    {
        "location": "Nea Makri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.9823, 38.1012]},
    },
    {
        "location": "Drosia, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8423, 38.1123]},
    },
    {
        "location": "Dionysos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8623, 38.1312]},
    },
    {
        "location": "Agios Stefanos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8723, 38.1412]},
    },
    {
        "location": "Kapandriti, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8112, 38.1912]},
    },
    {
        "location": "Elefsina, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.5423, 38.0434]},
    },
    {
        "location": "Mandra, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.5012, 38.0712]},
    },
    {
        "location": "Megara, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.3423, 37.9934]},
    },
    {
        "location": "Aspropirgos, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.5823, 38.0623]},
    },
    {
        "location": "Magoula, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.5612, 38.0534]},
    },
    {
        "location": "Kifisias 44, Marousi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8023, 38.0523]},
    },
    {
        "location": "Vouliagmenis 200, Ilioupoli, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7667, 37.9301]},
    },
    {
        "location": "Poseidonos 12, Glyfada, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7489, 37.8756]},
    },
    {
        "location": "Dimokratias 5, Galatsi, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7378, 38.0189]},
    },
    {
        "location": "Doiranis 30, Nea Smyrni, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7151, 37.9463]},
    },
    {
        "location": "Thivon 228, Egaleo, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6756, 37.9967]},
    },
    {
        "location": "Konstantinoupoleos 80, Peristeri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.6845, 38.0178]},
    },
    {
        "location": "Agias Paraskevis 50, Chalandri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.8034, 38.0189]},
    },
    {
        "location": "Marathonos 101, Nea Makri, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.9801, 38.0989]},
    },
    {
        "location": "Eleftheriou Venizelou 72, Kallithea, Athens",
        "coordinates": {"type": "Point", "coordinates": [23.7012, 37.9545]},
    },
    {
        "location": "Kalamaria, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9534, 40.5934]},
    },
    {
        "location": "Pylaia, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9923, 40.5912]},
    },
    {
        "location": "Panorama, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9823, 40.6312]},
    },
    {
        "location": "Chortiatis, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [23.0423, 40.6212]},
    },
    {
        "location": "Efkarpia, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9123, 40.7012]},
    },
    {
        "location": "Polichni, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9234, 40.6823]},
    },
    {
        "location": "Kordelio, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9012, 40.6623]},
    },
    {
        "location": "Menemeni, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.8812, 40.6712]},
    },
    {
        "location": "Diavata, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.8534, 40.7012]},
    },
    {
        "location": "Lagkadas, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [23.0712, 40.7512]},
    },
    {
        "location": "Triandria, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9634, 40.6234]},
    },
    {
        "location": "Sykies, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9512, 40.6534]},
    },
    {
        "location": "Oreokastro, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9178, 40.7268]},
    },
    {
        "location": "Agios Athanasios, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.8934, 40.5512]},
    },
    {
        "location": "Epanomi, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9323, 40.4312]},
    },
    {
        "location": "Peraia, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9212, 40.4623]},
    },
    {
        "location": "Nea Michaniona, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.8712, 40.4512]},
    },
    {
        "location": "Vasilika, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [23.1012, 40.5312]},
    },
    {
        "location": "Xanthi",
        "coordinates": {"type": "Point", "coordinates": [24.8912, 41.1334]},
    },
    {
        "location": "Drama",
        "coordinates": {"type": "Point", "coordinates": [24.1489, 41.1523]},
    },
    {
        "location": "Tsimiski 45, Thessaloniki Centre",
        "coordinates": {"type": "Point", "coordinates": [22.9454, 40.6334]},
    },
    {
        "location": "Egnatia 100, Thessaloniki Centre",
        "coordinates": {"type": "Point", "coordinates": [22.9534, 40.6389]},
    },
    {
        "location": "Monastiriou 65, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9312, 40.6412]},
    },
    {
        "location": "Lagkada 150, Stavroupoli, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9143, 40.6724]},
    },
    {
        "location": "Karaoli 20, Kalamaria, Thessaloniki",
        "coordinates": {"type": "Point", "coordinates": [22.9534, 40.5934]},
    },
    {
        "location": "Heraklion, Crete",
        "coordinates": {"type": "Point", "coordinates": [25.1442, 35.3387]},
    },
    {
        "location": "Chania, Crete",
        "coordinates": {"type": "Point", "coordinates": [24.0133, 35.5138]},
    },
    {
        "location": "Rethymno, Crete",
        "coordinates": {"type": "Point", "coordinates": [24.4750, 35.3612]},
    },
    {
        "location": "Agios Nikolaos, Crete",
        "coordinates": {"type": "Point", "coordinates": [25.7212, 35.1912]},
    },
    {
        "location": "Rhodes Town, Rhodes",
        "coordinates": {"type": "Point", "coordinates": [28.2273, 36.4412]},
    },
    {
        "location": "Kos Town, Kos",
        "coordinates": {"type": "Point", "coordinates": [27.2873, 36.8934]},
    },
    {
        "location": "Patras",
        "coordinates": {"type": "Point", "coordinates": [21.7346, 38.2466]},
    },
    {
        "location": "Volos",
        "coordinates": {"type": "Point", "coordinates": [22.9678, 39.3667]},
    },
    {
        "location": "Ioannina",
        "coordinates": {"type": "Point", "coordinates": [20.8553, 39.6650]},
    },
    {
        "location": "Kavala",
        "coordinates": {"type": "Point", "coordinates": [24.4100, 40.9396]},
    },
    {
        "location": "Alexandroupoli",
        "coordinates": {"type": "Point", "coordinates": [25.8756, 40.8453]},
    },
    {
        "location": "Katerini",
        "coordinates": {"type": "Point", "coordinates": [22.5011, 40.2714]},
    },
    {
        "location": "Chalkida",
        "coordinates": {"type": "Point", "coordinates": [23.5971, 38.4634]},
    },
    {
        "location": "Tripoli, Arcadia",
        "coordinates": {"type": "Point", "coordinates": [22.3790, 37.5100]},
    },
    {
        "location": "Korinthos",
        "coordinates": {"type": "Point", "coordinates": [22.9295, 37.9387]},
    },
    {
        "location": "Nafplio",
        "coordinates": {"type": "Point", "coordinates": [22.8011, 37.5678]},
    },
    {
        "location": "Zakynthos Town",
        "coordinates": {"type": "Point", "coordinates": [20.8923, 37.7879]},
    },
    {
        "location": "Kerkyra (Corfu Town)",
        "coordinates": {"type": "Point", "coordinates": [19.9210, 39.6243]},
    },
    {
        "location": "Mytilini, Lesbos",
        "coordinates": {"type": "Point", "coordinates": [26.5540, 39.1101]},
    },
    {
        "location": "Syros Town (Ermoupoli)",
        "coordinates": {"type": "Point", "coordinates": [24.9423, 37.4423]},
    },
]

issue_descriptions = [
    {
        "title": "Large Pothole Causing Vehicle Damage",
        "description": "A large pothole is causing damage to vehicles and posing a safety hazard to cyclists and pedestrians passing through.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Street Light Out Of Service",
        "description": "A street light has been non-functional for several days, leaving the surrounding area completely dark during nighttime hours.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Illegal Waste Dumping Detected",
        "description": "Large amounts of household and construction waste have been illegally dumped, creating an environmental and public health hazard.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Flooded Road After Heavy Rain",
        "description": "Heavy rainfall has caused significant water accumulation, making the area impassable for both vehicles and pedestrians.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Graffiti Vandalism On Public Property",
        "description": "Extensive graffiti tags have been applied to a public building facade, causing visible damage and reducing the area's appearance.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Fallen Tree Blocking Pedestrian Path",
        "description": "A large tree has fallen across a pedestrian path following a storm, completely blocking access and damaging surrounding infrastructure.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Strong Gas Odor Reported By Residents",
        "description": "Multiple residents have reported a strong smell of gas in the area, the source of which is currently unknown and potentially dangerous.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Playground Equipment Risk",
        "description": "Playground equipment has broken and exposed sharp metal edges, posing a serious injury risk to children using the area.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Blocked Drain Causing Street Flooding",
        "description": "A blocked storm drain is causing water to overflow onto the road and nearby properties during moderate to heavy rainfall.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Abandoned Vehicle Left On Street",
        "description": "A vehicle has been abandoned and left unattended for several days, obstructing traffic flow and taking up public parking space.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Water Main Leaking",
        "description": "A water main is visibly leaking and causing water to pool on the surface, potentially damaging the road structure and wasting public resources.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Dangerous Exposed Electrical Wiring",
        "description": "Electrical wiring has been left exposed following recent maintenance work, posing a serious electrocution risk to pedestrians and nearby residents.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overflowing Public Rubbish Bins",
        "description": "Public rubbish bins have been overflowing for several days, attracting pests and creating an unsanitary environment for the surrounding area.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Cracked And Uneven Pavement",
        "description": "Severely cracked and uneven pavement is creating a significant trip hazard for pedestrians, particularly the elderly and those with mobility issues.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Stray Animals Causing Disturbance",
        "description": "A group of stray animals has been frequently spotted in the area, causing disturbances and posing a potential safety risk to residents and children.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Missing Manhole Cover On Road",
        "description": "A manhole cover is missing, leaving a dangerous open hole in the road that poses an extreme risk to vehicles, cyclists and pedestrians.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Road Signs Causing Confusion",
        "description": "Several road signs have been damaged or knocked down, causing confusion for drivers and creating a potential risk for traffic accidents.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Sewage Smell Coming From Drains",
        "description": "A strong sewage smell is emanating from nearby drains, suggesting a possible blockage or damage to the underground sewage system.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Bus Shelter Glass Panel",
        "description": "A glass panel in a public bus shelter has been shattered, leaving sharp shards exposed and posing an injury risk to commuters using the stop.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Faulty Traffic Lights At Junction",
        "description": "Traffic lights are malfunctioning and displaying incorrect signals, causing confusion among drivers and increasing the risk of collisions at the junction.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Shots Fired At Local Park",
        "description": "Many shots were fired by 3 individuals resulting in chaos in the neighborhood.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Apartment Robbery Nearby",
        "description": "A robbery occurred by 2 individuals in a neighboring apartment.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Armed Robbery At Convenience Store",
        "description": "Two masked individuals armed with weapons robbed a local convenience store and fled on foot. Clerk sustained minor injuries.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Suspected Drug Dealing In Public Area",
        "description": "Residents have repeatedly observed individuals exchanging substances in a public square, with suspicious activity occurring mostly late at night.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Physical Assault Outside Nightclub",
        "description": "A violent altercation broke out between several individuals outside a nightclub, resulting in at least one person requiring medical attention.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Vehicle Break-In And Theft",
        "description": "Multiple parked vehicles in a residential street had their windows smashed and valuables stolen overnight.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Domestic Disturbance With Loud Arguing",
        "description": "Neighbors have reported ongoing loud arguing and sounds of objects being thrown from a nearby apartment, raising concerns about occupant safety.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Suspected Stolen Vehicle Parked Nearby",
        "description": "A vehicle with no plates and a damaged ignition has been parked in the same spot for days, suspected to be stolen.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Vandalism And Property Destruction",
        "description": "A group of individuals was seen intentionally smashing shop windows and damaging parked cars along a commercial street late at night.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Pickpocketing Reports At Bus Station",
        "description": "Several commuters have reported having their wallets and phones stolen at the local bus station, likely by an organized pickpocketing group.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Threatening Behavior Toward Residents",
        "description": "A resident has been repeatedly threatened and intimidated by a neighbor, causing significant fear and distress.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Illegal Street Racing Reported",
        "description": "Residents have reported repeated illegal street racing on a main road late at night, posing a severe danger to other road users.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Suspicious Package Left Unattended",
        "description": "An unattended bag or package has been left in a public area for an extended period, causing concern among nearby residents and passersby.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Shoplifting Incident At Supermarket",
        "description": "Staff at a local supermarket have reported repeated shoplifting incidents by the same individual, who has become increasingly aggressive when confronted.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Missing Person Report",
        "description": "A family member has reported a person missing after they failed to return home and cannot be reached by phone.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Noise Complaint From Illegal Gathering",
        "description": "A large unauthorized gathering is taking place in a private property, generating excessive noise and causing disturbances to the surrounding neighborhood.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Trespassing On Private Property",
        "description": "Unknown individuals have been repeatedly spotted entering a private property without authorization, raising concerns about potential burglary.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Hit And Run Accident Reported",
        "description": "A driver struck a parked vehicle and a pedestrian before fleeing the scene. The pedestrian sustained injuries and witnesses recorded a partial plate number.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Harassment Of Elderly Resident",
        "description": "An elderly resident has been repeatedly harassed and followed by unknown individuals when returning home, leaving them afraid to go outside.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Public Intoxication And Disorderly Conduct",
        "description": "Heavily intoxicated individuals are causing a disturbance in a public area, becoming verbally abusive and blocking pedestrian access.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Bicycle Theft From Public Rack",
        "description": "Several bicycles secured to a public rack were stolen overnight. CCTV footage from nearby businesses may have captured the perpetrators.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Fraud Attempt Targeting Local Businesses",
        "description": "Multiple local business owners have reported being approached by individuals posing as city inspectors and demanding cash payments to avoid fines.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Road Rage Incident With Weapon Involved",
        "description": "A road rage altercation escalated with one driver brandishing a weapon at another motorist before speeding away.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Knife Fight Between Two Individuals",
        "description": "Witnesses reported a knife fight between two individuals near a residential building. One person appears injured and requires immediate medical assistance.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Illegal Dumping Of Hazardous Chemicals",
        "description": "Barrels containing unknown chemicals have been illegally dumped in an open area, posing a serious environmental and public health risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Collapsed Retaining Wall On Footpath",
        "description": "A retaining wall along a public footpath has partially collapsed, blocking the path and posing a risk of further collapse onto passersby.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Public Bench In Park",
        "description": "A public bench in a local park has broken and collapsed, leaving sharp protruding metal parts that could injure park visitors.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overgrown Vegetation Blocking Visibility",
        "description": "Overgrown trees and shrubs at a road junction are obstructing driver sightlines, creating a significant hazard for traffic turning at the intersection.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Public Water Fountain",
        "description": "A public water fountain has been vandalized and is now continuously running, wasting water and making the surrounding area slippery and unsafe.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Construction Debris Left On Public Road",
        "description": "A construction crew has left large amounts of debris and materials on a public road without barriers or signage, creating a hazard for vehicles and pedestrians.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Speeding Vehicles On Leoforos Kifisias",
        "description": "Drivers are consistently exceeding speed limits on Leoforos Kifisias, posing a serious danger to pedestrians crossing at unmarked points and cyclists using the road.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Illegal Parking Blocking Bus Lane On Vouliagmenis",
        "description": "Multiple vehicles are illegally parked in the dedicated bus lane on Leoforos Vouliagmenis, causing significant delays to public transport and blocking emergency vehicle access.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Collapsed Pavement Slab On Iera Odos",
        "description": "A large pavement slab has collapsed near Iera Odos 45 in Egaleo, leaving a deep gap that poses a serious fall risk particularly for elderly pedestrians and cyclists.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Street Brawl Outside Shop On Leoforos Athinon",
        "description": "A violent brawl between a group of individuals broke out outside a shop on Leoforos Athinon in Peristeri, with witnesses reporting the use of bottles as weapons.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Broken Street Lighting On Liosion Street",
        "description": "Several consecutive street lights on Liosion in Kato Patisia have been non-functional for over a week, leaving a long stretch of the road completely unlit at night.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Suspected Drug Activity Near Alexandras Avenue",
        "description": "Residents near Alexandras 132 have reported repeated suspicious exchanges between individuals in parked vehicles late at night, strongly suggesting drug dealing activity.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Overflowing Sewage On Patision Street",
        "description": "A sewage pipe appears to have burst near Patision 201 in Ano Patisia, causing foul-smelling waste water to overflow onto the pavement and road surface.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Aggressive Panhandling On Syngrou Avenue",
        "description": "Residents and commuters near Syngrou 95 have reported being aggressively approached and intimidated by individuals demanding money, making them feel unsafe.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Large Pothole On Pireos Street Near Tavros",
        "description": "A large and deep pothole has formed on Pireos 180 in Tavros, already causing damage to several vehicles and posing a risk of accidents especially for motorcyclists.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Unauthorized Dumping Of Construction Waste On Mesogeion",
        "description": "Large quantities of construction rubble and waste materials have been dumped illegally on the pavement near Mesogeion 256 in Holargos, blocking pedestrian access entirely.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Traffic Barrier On Kifisias Avenue, Marousi",
        "description": "A concrete traffic barrier along Kifisias 44 in Marousi has been partially destroyed, likely from a vehicle collision, leaving sharp debris scattered across the lane.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Flooded Underpass In Moschato",
        "description": "Heavy rain has caused the pedestrian underpass in Moschato to fill with water, making it completely impassable and forcing pedestrians onto a dangerous road junction.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Abandoned Construction Site Attracting Trespassers In Glyfada",
        "description": "An unsecured abandoned construction site in Glyfada has no fencing or warning signs, and children have been spotted entering the site, posing serious injury risks.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Illegal Dumping Near Elefsina Industrial Zone",
        "description": "Large quantities of industrial and household waste have been illegally dumped on the outskirts of Elefsina, creating a significant environmental and public health hazard.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Street Light Outage Across Multiple Blocks In Vyronas",
        "description": "An entire stretch of road in Vyronas has been without street lighting for several nights, making the area dangerous for pedestrians and cyclists after dark.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Crumbling Retaining Wall On Hillside Road In Kaisariani",
        "description": "A retaining wall along a hillside road in Kaisariani is visibly crumbling and showing signs of imminent collapse, threatening both traffic below and neighbouring properties.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overflowing Rubbish Bins Near Kifisia Metro Station",
        "description": "Public bins near the Kifisia metro station have been overflowing for several days, attracting rodents and creating an unsanitary environment for commuters.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Pothole Cluster On Main Road Through Nea Ionia",
        "description": "A series of large potholes has formed on the main road through Nea Ionia following recent heavy rain, causing damage to vehicles and posing a hazard to motorcyclists.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Pavement Slabs Outside School In Galatsi",
        "description": "Severely cracked and uplifted pavement slabs outside a primary school in Galatsi are creating a serious trip hazard for children arriving and leaving school each day.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Uprooted Tree Blocking Cycle Lane In Chalandri",
        "description": "A large tree has been uprooted and fallen across the dedicated cycle lane in Chalandri, forcing cyclists into live traffic and creating a significant safety risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Burst Water Pipe Flooding Road In Nea Filadelfia",
        "description": "A burst underground water pipe is flooding the road surface in Nea Filadelfia, making it impassable for vehicles and creating a slipping hazard for pedestrians.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Graffiti Covering Bus Stop In Irakleio",
        "description": "A public bus stop in Irakleio has been extensively covered in graffiti tags, damaging the shelter and making timetable information completely unreadable.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Collapsed Drain Cover In Metamorfosi",
        "description": "A drain cover on a busy road in Metamorfosi has collapsed inward, creating a deep open hole that poses an extreme hazard to passing cyclists and vehicles.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overgrown Vegetation Blocking Footpath In Ekali",
        "description": "Unmanaged overgrowth from a private estate in Ekali has completely encroached onto the adjacent public footpath, forcing pedestrians to walk on the road.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Public Lighting Pole In Nea Erythraia",
        "description": "A street lighting pole in Nea Erythraia has been struck by a vehicle and is leaning dangerously over the pavement, with electrical cabling visibly exposed at its base.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Blocked Storm Drain Causing Flooding In Agios Dimitrios",
        "description": "A blocked storm drain in Agios Dimitrios is causing water to pool across the road and spill into residential properties during moderate rainfall.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Fence Around Children's Park In Pefki",
        "description": "The perimeter fence of a children's playground in Pefki has broken in multiple sections, allowing uncontrolled access and posing a risk to young children playing near the road.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Sewage Overflow On Residential Street In Lykovrysi",
        "description": "A sewage overflow has been reported on a residential street in Lykovrysi, with foul-smelling wastewater surfacing from a blocked drain and spreading across the pavement.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Dangerous Crack In Road Bridge In Aspropirgos",
        "description": "A visible structural crack has appeared on a road bridge in Aspropirgos. Local residents are concerned about the bridge's integrity and its safety for heavy vehicles.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Abandoned Chemical Barrels Near Industrial Area In Mandra",
        "description": "Several unmarked barrels suspected of containing chemical substances have been abandoned near an industrial site in Mandra, raising serious environmental and safety concerns.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Faulty Traffic Lights Causing Gridlock In Papagou",
        "description": "Traffic lights at a busy junction in Papagou are cycling too rapidly and displaying conflicting signals, causing significant gridlock and increasing accident risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Stray Dog Pack Causing Disturbances In Voula",
        "description": "A large pack of stray dogs has been frequenting a residential neighbourhood in Voula, aggressively approaching residents and posing a particular risk to children and the elderly.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Road Markings On Coastal Road In Vouliagmeni",
        "description": "Road lane markings along the coastal road in Vouliagmeni have worn away almost completely, causing confusion for drivers especially at night and in wet conditions.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overflowing Septic System Near Homes In Vari",
        "description": "A communal septic tank near a housing cluster in Vari appears to have overflowed, releasing effluent into a nearby stream and creating a serious public health risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Derelict Building Attracting Squatters In Egaleo",
        "description": "A long-derelict multi-storey building in Egaleo has become occupied by unknown individuals. Broken windows and structural damage make the building hazardous to occupants and neighbours.",
        "urgent": False,
        "department": "POLICE",
    },
    # Athens police matters
    {
        "title": "Repeated Car Break-Ins In Kifisia Residential Area",
        "description": "Residents in a Kifisia neighbourhood have reported a wave of overnight car break-ins, with at least eight vehicles targeted over the past two weeks.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Aggressive Harassment Outside Nightclub In Glyfada",
        "description": "Multiple complaints have been filed about aggressive individuals outside a nightclub in Glyfada who are harassing passersby and blocking pedestrian access on the pavement.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Illegal Street Market Operating In Nea Ionia",
        "description": "An unlicensed street market has been operating on a main road in Nea Ionia for several weeks, obstructing traffic and generating complaints from licensed neighbouring businesses.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Suspected Burglary In Progress In Chalandri",
        "description": "A neighbour has reported seeing an individual forcing entry through a ground-floor window of a residential property in Chalandri while the occupants appear to be away.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Drunk Driver Swerving On Road In Voula",
        "description": "Witnesses have reported a driver swerving erratically through traffic in Voula late at night, nearly colliding with two pedestrians and running a red light.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Organized Shoplifting Group Operating In Glyfada",
        "description": "Multiple retailers in central Glyfada have reported coordinated shoplifting by what appears to be an organized group of individuals operating across several stores simultaneously.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Trespassing And Vandalism At Abandoned Factory In Aspropirgos",
        "description": "Groups of individuals have been regularly breaking into an abandoned factory in Aspropirgos, vandalizing the premises and causing structural damage to an already unstable building.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Domestic Violence Incident Reported In Vyronas",
        "description": "Neighbours in Vyronas have called to report repeated sounds of violence and screaming from an apartment, raising serious concerns for the safety of the occupants.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Illegal Gambling Den Reported In Egaleo",
        "description": "Local residents have reported the regular gathering of many individuals in a ground-floor commercial property in Egaleo that appears to be operating as an illegal gambling den.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Road Rage Assault Near Elliniko",
        "description": "A motorist was physically assaulted by another driver following a minor traffic dispute near Elliniko. The victim sustained facial injuries and the aggressor drove away.",
        "urgent": True,
        "department": "POLICE",
    },
    # Thessaloniki municipalities
    {
        "title": "Large Pothole On Tsimiski Street, Thessaloniki Centre",
        "description": "A large and deepening pothole has formed on Tsimiski street in the city centre, causing repeated damage to passing vehicles and creating a hazard for cyclists.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Blocked Drain Causing Flooding On Egnatia, Thessaloniki",
        "description": "A blocked drain on Egnatia 100 is causing severe water pooling during rain, flooding the pavement and making the nearby pedestrian subway dangerously slippery.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Collapsed Pavement On Monastiriou Street, Thessaloniki",
        "description": "A section of pavement on Monastiriou street has collapsed inward, exposing an underground cavity. The area has no barriers or warning signs, posing a serious fall risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overflowing Bins In Kalamaria, Thessaloniki",
        "description": "Public waste bins in a residential area of Kalamaria have been overflowing for multiple days, attracting pests and generating complaints from local residents about hygiene.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Street Light In Panorama, Thessaloniki",
        "description": "A key street light on the main road through Panorama has been non-functional for over a week, leaving a blind bend completely unlit and dangerous for drivers at night.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Illegal Waste Dump Discovered In Diavata, Thessaloniki",
        "description": "Large amounts of construction and household waste have been illegally dumped on an open plot in Diavata, creating an environmental hazard and attracting vermin.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Guardrail On Mountain Road Near Chortiatis",
        "description": "A guardrail on the winding mountain road near Chortiatis has been badly damaged, leaving a section of the road completely unprotected at a sharp drop-off.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Water Main Leak Flooding Road In Pylaia, Thessaloniki",
        "description": "A broken water main in Pylaia is causing significant surface flooding on a main road, eroding the road surface and creating hazardous driving conditions.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Cracked And Subsiding Road Surface In Sykies, Thessaloniki",
        "description": "A long section of road surface in Sykies is subsiding and cracking severely, likely due to underground drainage issues, posing a risk of sudden collapse.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overhanging Tree Branches Blocking Road Signs In Triandria",
        "description": "Overgrown tree branches in Triandria are completely obscuring multiple road and directional signs, causing confusion for drivers unfamiliar with the area.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Public Bench And Scattered Glass In Neapoli, Thessaloniki",
        "description": "A public bench in a park in Neapoli has been destroyed, with broken wooden slats and shattered glass spread across the surrounding area, posing injury risks to children.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Faulty Traffic Lights At Junction In Kordelio, Thessaloniki",
        "description": "Traffic lights at a major junction in Kordelio have been malfunctioning for two days, showing simultaneous green signals in conflicting directions and causing near-collisions.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Sewage Smell From Drains In Stavroupoli, Thessaloniki",
        "description": "A persistent and strong sewage odour has been emanating from multiple drain covers in Stavroupoli, suggesting a significant blockage or rupture in the underground sewer system.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Dangerous Exposed Wiring At Bus Stop In Evosmos, Thessaloniki",
        "description": "Electrical wiring is exposed at a public bus stop in Evosmos following vandalism. The wiring is within reach of passengers waiting at the stop and poses an electrocution risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Graffiti Covering Historic Building Facade In Thessaloniki Centre",
        "description": "Extensive graffiti has been applied overnight to the facade of a listed historic building near Egnatia street, causing cultural and aesthetic damage to the city's heritage area.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Flooded Road After Storm In Efkarpia, Thessaloniki",
        "description": "A major road in Efkarpia is completely flooded following a storm, with water levels too deep for standard vehicles and no emergency signage or barriers in place.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Abandoned Vehicle Blocking Lane In Menemeni, Thessaloniki",
        "description": "A vehicle with no license plates has been abandoned in a live traffic lane in Menemeni for several days, causing congestion and creating a hazard for other road users.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Collapsed Pavement Near School In Polichni, Thessaloniki",
        "description": "A section of pavement directly outside a primary school in Polichni has collapsed, leaving a dangerous gap in the path used by hundreds of children each school day.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Missing Manhole Cover On Road In Ampelokipoi, Thessaloniki",
        "description": "A manhole cover is missing on a busy road in Ampelokipoi, leaving an open hole with no barriers or warning signs. Motorcyclists are at particular risk of serious injury.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Stray Animals Causing Disturbance Near Market In Oraiokastro",
        "description": "A large number of stray dogs and cats have been congregating near a local market in Oraiokastro, frightening shoppers and children and creating sanitation concerns.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    # Thessaloniki police matters
    {
        "title": "Assault And Robbery Near Tsimiski Street, Thessaloniki",
        "description": "A pedestrian was assaulted and robbed near Tsimiski street in the early hours of the morning. The victim was punched and had a bag containing valuables stolen.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Illegal Street Racing Reported In Kalamaria, Thessaloniki",
        "description": "Residents of Kalamaria have repeatedly reported illegal street racing late at night on a long straight road near the waterfront, causing extreme danger to other road users.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Suspected Drug Dealing Activity In Stavroupoli, Thessaloniki",
        "description": "Residents near Lagkada street in Stavroupoli have been reporting repeated suspicious exchanges between individuals in a specific alleyway, particularly during late night hours.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Vehicle Break-Ins Overnight In Sykies, Thessaloniki",
        "description": "At least five vehicles parked in a residential street in Sykies had their windows smashed and contents stolen overnight, with the incidents concentrated on the same block.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Violent Altercation Outside Bar In Neapoli, Thessaloniki",
        "description": "A violent fight broke out between multiple individuals outside a bar in Neapoli, with witnesses reporting the use of a glass bottle as a weapon and at least one person injured.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Pickpocketing Gang Operating At Thessaloniki Train Station",
        "description": "Multiple travellers at Thessaloniki's central train station have reported having phones and wallets stolen, with descriptions pointing to a coordinated group of at least three individuals.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Threatening Behavior By Neighbor In Evosmos, Thessaloniki",
        "description": "A resident in Evosmos has formally reported being repeatedly threatened and physically intimidated by a neighbour over a property boundary dispute, causing them significant distress.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Hit And Run Incident On Monastiriou, Thessaloniki",
        "description": "A cyclist was struck by a vehicle on Monastiriou street and the driver fled the scene without stopping. The cyclist suffered leg injuries and was taken to hospital by bystanders.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Burglary Reported At Commercial Property In Pylaia, Thessaloniki",
        "description": "The owner of a commercial property in Pylaia arrived at their premises to find a forced entry and multiple items stolen. Security cameras were disabled prior to the break-in.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Public Intoxication Causing Disturbance Near Port, Thessaloniki",
        "description": "A group of heavily intoxicated individuals near the port area of Thessaloniki are causing a significant disturbance, harassing passersby and obstructing the entrance to a public building.",
        "urgent": False,
        "department": "POLICE",
    },
    # Other cities
    {
        "title": "Burst Water Main Flooding Street In Heraklion, Crete",
        "description": "A water main has burst on a central street in Heraklion, flooding the road and cutting water supply to dozens of surrounding homes and businesses.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Overflowing Rubbish Bins In Chania Old Town, Crete",
        "description": "Bins throughout the historic old town of Chania have been overflowing for several days, creating unsanitary conditions in a high-footfall tourist area during peak season.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Damaged Road Surface On National Highway Near Patras",
        "description": "A significant section of the national highway approaching Patras has developed severe surface cracking and subsidence, posing a danger to vehicles at highway speeds.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Illegal Parking Blocking Emergency Access In Volos",
        "description": "Vehicles are habitually parked illegally in front of a fire station in Volos, obstructing emergency vehicle access and repeatedly delaying emergency response times.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Street Light Outage On Major Road In Larissa",
        "description": "Multiple consecutive street lights on a main arterial road in Larissa have been non-functional for over two weeks, making the road extremely hazardous at night.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Assault And Robbery Near University In Ioannina",
        "description": "A student was assaulted and robbed near the university campus in Ioannina late at night. Witnesses described two attackers who fled toward the city centre.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Fallen Tree Blocking Road After Storm In Kavala",
        "description": "A large tree has been brought down by storm winds and is blocking a main road in Kavala, preventing all traffic and requiring immediate removal by municipal services.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Illegal Dumping Of Waste On Beach Access Road In Rhodes",
        "description": "Construction waste and household rubbish have been illegally dumped on a public access road to a beach in Rhodes, blocking the path and creating an environmental hazard.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Drug Dealing Activity Reported Near Port In Piraeus",
        "description": "Residents and business owners near the port in Piraeus have reported a persistent presence of individuals suspected of dealing drugs in an underpass used by commuters.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Cracked Pavement Creating Trip Hazard In Korinthos",
        "description": "Large sections of pavement in central Korinthos have heaved and cracked severely, creating multiple serious trip hazards particularly for elderly residents and tourists.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Vandalism Of Public Fountains In Nafplio",
        "description": "Several decorative public fountains in Nafplio's historic centre have been vandalized overnight, with pipes damaged and water running uncontrollably into the street.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Speeding Motorcycles On Seafront Road In Kerkyra",
        "description": "Tourists and residents along the Corfu Town seafront have reported motorcyclists travelling at dangerous speeds on a road shared with pedestrians and cyclists.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Abandoned Vessel Causing Navigation Hazard In Mytilini Harbour",
        "description": "A partially sunken abandoned vessel in Mytilini harbour is obstructing navigation channels and leaking oil onto the water surface, posing an environmental and safety risk.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Missing Road Signs On Mountain Pass Near Florina",
        "description": "Several directional and warning road signs are missing on a mountain pass near Florina, creating dangerous confusion for drivers unfamiliar with the route, especially in winter conditions.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Physical Altercation At Taxi Rank In Alexandroupoli",
        "description": "A violent fight broke out between drivers at a busy taxi rank in Alexandroupoli during peak hours, resulting in injuries to two individuals and significant disruption to traffic.",
        "urgent": True,
        "department": "POLICE",
    },
    # Additional Athens entries
    {
        "title": "Crumbling Staircase In Public Park In Penteli",
        "description": "Stone steps on a public park path in Penteli have crumbled significantly, with multiple steps now missing or collapsed, making the path extremely dangerous for elderly visitors.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Broken Traffic Lights Causing Near-Miss In Gerakas",
        "description": "Traffic lights at a busy crossroads in Gerakas have been completely dark for over 24 hours following a power fault, resulting in several near-miss collisions.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Flooded Basement Garage After Pipe Burst In Pallini",
        "description": "A municipal water pipe has burst near a residential building in Pallini, causing extensive flooding of a shared underground garage and cutting water supply to the building.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Aggressive Behavior And Threats At Rafina Ferry Port",
        "description": "Several travellers at the Rafina ferry port have reported being aggressively approached and verbally threatened by individuals loitering near the ticketing area.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Illegal Waste Burning On Vacant Lot In Acharnes",
        "description": "Residents of Acharnes have reported repeated burning of mixed waste including plastics on a vacant lot, producing toxic smoke that is affecting air quality across the neighbourhood.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Vandalized Public Toilet Facility In Marathonas",
        "description": "The public toilet facility near the Marathon archaeological site has been vandalized, with fixtures destroyed and the facility left unusable, impacting visitors to the area.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Suspicious Individuals Casing Properties In Drosia",
        "description": "Multiple residents in Drosia have independently reported the same individuals repeatedly walking past and photographing private homes, raising concerns about planned burglaries.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Collapsed Fence Onto Public Footpath In Nea Makri",
        "description": "A wooden boundary fence alongside a public footpath in Nea Makri has collapsed entirely onto the path, blocking it completely and making the only alternative route along the road.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Repeated Noise Nuisance From Unlicensed Venue In Argyroupoli",
        "description": "Residents near Leoforos Vouliagmenis in Argyroupoli have submitted multiple complaints about an apparent unlicensed events venue operating past midnight and generating excessive noise.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Gas Odor Reported Near Apartment Block In Peristeri",
        "description": "Residents of a multi-storey apartment block in Peristeri have reported a persistent smell of gas in the building's stairwell, the source of which has not yet been identified.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    # Additional Thessaloniki entries
    {
        "title": "Subsidence Crack Appearing Across Road In Thermi",
        "description": "A long crack consistent with underground subsidence has appeared across a road in Thermi, widening noticeably over recent days and causing concern about a potential road collapse.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Missing Pedestrian Crossing Markings Near School In Lagkadas",
        "description": "Pedestrian crossing markings outside a school in Lagkadas have worn away completely, leaving children with no visible crossing protection on a busy road.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Stolen Motorbike Reportedly Seen In Peraia, Thessaloniki",
        "description": "The owner of a stolen motorbike has reported spotting their vehicle parked in a residential area of Peraia, with the plates changed. They have not approached the vehicle.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Dangerous Overspeed Of Vehicles On Coastal Road In Epanomi",
        "description": "Residents and cyclists in Epanomi have raised repeated concerns about vehicles travelling far above the speed limit on the coastal road, particularly late at night and on weekends.",
        "urgent": False,
        "department": "POLICE",
    },
    {
        "title": "Gas Leak Reported In Commercial Building In Ampelokipoi, Thessaloniki",
        "description": "Staff at a commercial building in Ampelokipoi, Thessaloniki detected a strong smell of gas in the ground floor. The building has been partially evacuated pending inspection.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    # Additional other cities
    {
        "title": "Illegal Fishing With Explosives Reported Off Coast Near Kavala",
        "description": "Fishermen near Kavala have reported witnessing a boat using explosive devices for illegal fishing, destroying marine habitat and posing a significant danger to other boats in the area.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Pothole Damage On Main Street In Trikala",
        "description": "A cluster of potholes on the main commercial street in Trikala has been causing damage to vehicles for several weeks, with multiple residents submitting repair requests without response.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Sewage Backing Up Into Gardens In Volos Suburb",
        "description": "Homeowners in a residential suburb of Volos have reported sewage backing up through drain pipes into their gardens, indicating a serious blockage in the main municipal sewer line.",
        "urgent": True,
        "department": "MUNICIPALITY",
    },
    {
        "title": "Assault Of Tourist Reported In Rhodes Old Town",
        "description": "A tourist was assaulted and had their bag snatched in a narrow alleyway in the Rhodes Old Town. The victim sustained minor injuries and the assailant fled on foot.",
        "urgent": True,
        "department": "POLICE",
    },
    {
        "title": "Unlit Pedestrian Bridge Causing Safety Concerns In Katerini",
        "description": "A pedestrian footbridge in Katerini has been without lighting for over three weeks. Residents report near-falls after dark and fear the bridge is being used for antisocial activity at night.",
        "urgent": False,
        "department": "MUNICIPALITY",
    },
]


async def fill_data() -> None:
    http = _http_client
    data = []

    assert len(locations) == len(issue_descriptions)
    for i in range(len(locations)):
        data.append(locations[i])
        data[i].update(issue_descriptions[i])

    response = await http.post(
        "/reports/batch",
        json=data,
        headers={"Authorization": ""},
    )
    print(response.json())


if __name__ == "__main__":
    asyncio.run(fill_data())
