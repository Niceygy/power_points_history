import datetime
import requests, json
from tqdm import tqdm
from matplotlib import pyplot as plt
import bz2, os
import concurrent.futures

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
    if not os.path.exists(f"data/{ED_GALAXY_URL}"):
        data = requests.get(f"https://edgalaxydata.space/EDDN/2025-06/{ED_GALAXY_URL}", stream=True)
        print(f"Loading data from {ED_GALAXY_URL}")
        with open(f"data/{ED_GALAXY_URL}", "wb") as f:
            f.write(bz2.decompress(data.raw.read()))
    print("Loaded")
    data = open(f"data/{ED_GALAXY_URL}", "rb").read()
    lines = []
    for line in tqdm(data.split(b"\n"), desc="Decompressing", unit=" lines"):
        if line:
            lines.append(line.decode())
    data = lines

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
                # if "ControllingPower" in json_line["message"] and state != "Unoccupied":
                #     power = json_line["message"]["ControllingPower"]
                # elif "Powers" in json_line["message"]:
                #     power = json_line["message"]["Powers"][0]
                    

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


def addto(date):
    print(f"Date: {date} #######################################################################################")
    # _temp = dataed(f"https://edgalaxydata.space/EDDN/2025-06/Journal.FSDJump-2025-{date}.jsonl.bz2", system_name)
    _temp = dataed(f"Journal.FSDJump-2025-{date}.jsonl.bz2", system_name)
    times.append(date)
    for i in range(len(_temp)):
        ppoints.append(_temp[i]['pts'])
        times.append("")
        

dates = ["06-01", "06-02", "06-03", "06-04", "06-05", "06-06"]
for item in dates:
    addto(item)



times = times[6:]
plt.plot(times, ppoints)
plt.title(system_name)
plt.savefig(f"images/image_{system_name}.png")
