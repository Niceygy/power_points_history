import datetime
import requests, json
from tqdm import tqdm
from matplotlib import pyplot as plt
import bz2

system_name = input("Enter system name: ")


def corrected_control_pts(state: str, progress: float) -> float:
        """Corrects the control points for use in the db

        Args:
            state (str): system state
            progress (float): progress from journal

        Returns:
            float: Corrected control pts
        """
        if progress > 4000:
            if state == "Exploited":
                scale = 349999
            elif state == "Fortified":
                scale = 650000
            elif state == "Stronghold":
                scale = 1000000
            else: # must be "Unoccupied", never reached
                scale = 120000
            progress -= 4294967296 / scale
        return progress

def dataed(ED_GALAXY_URL, system_name):
    print(f"Loading data from {ED_GALAXY_URL}")
    data = requests.get(ED_GALAXY_URL, stream=True)
    print("Loaded")
    data = bz2.decompress(data.raw.read())
    lines = []
    for line in tqdm(data.split(b"\n"), desc="Decompressing", unit=" lines"):
        if line:
            lines.append(line.decode())
    data = lines
    total = len(data)

    last_date = None

    powerdata = []
    for item in data:
        json_line = json.loads(item)
        if system_name == json_line["message"]["StarSystem"]:

            message_timestamp = datetime.datetime.strptime(
                json_line["message"]["timestamp"], "%Y-%m-%dT%H:%M:%SZ"
            )
            if last_date is not None and last_date > message_timestamp:
                continue  # Skip older messages
            last_date = message_timestamp

            if "PowerplayState" in json_line["message"]:
                state = json_line["message"]["PowerplayState"]
                if "ControllingPower" in json_line["message"] and state != "Unoccupied":
                    power = json_line["message"]["ControllingPower"]
                elif "Powers" in json_line["message"]:
                    power = json_line["message"]["Powers"][0]
                    

                try:
                    points = corrected_control_pts(state=state, progress=json_line["message"]["PowerplayStateControlProgress"])
                    powerdata.append(
                    {
                        # "power": power,
                        "pts": float(points),
                        'times': json_line["message"]["timestamp"]
                        
                    }
                )
                except Exception:
                    None
    return powerdata

times = []
ppoints = []


def addto(ppoints, date):
    _temp = dataed(f"https://edgalaxydata.space/EDDN/2025-06/Journal.FSDJump-2025-{date}.jsonl.bz2", system_name)
    for i in range(len(_temp)):
        ppoints.append(_temp[i]['pts'])
        times.append(_temp[i]['times'])
    
addto(ppoints, "06-01")
addto(ppoints, "06-02")
addto(ppoints, "06-03")
addto(ppoints, "06-04")
addto(ppoints, "06-05")



iis = []
for item in times:
    iis.append(datetime.datetime.strptime(item, "%Y-%m-%dT%H:%M:%SZ"))


plt.plot(iis, ppoints)
plt.savefig("image_sol.png")
