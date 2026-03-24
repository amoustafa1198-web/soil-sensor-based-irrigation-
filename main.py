import os
import time
import requests

BASE_URL = "https://api.databoom.com/v1"
PUSH_URL = f"{BASE_URL}/signals/push"
SIGNALS_URL = f"{BASE_URL}/signals/"

TOKEN = os.getenv("DATABOOM_TOKEN")
if not TOKEN:
    raise RuntimeError("DATABOOM_TOKEN is not set")

THRESHOLD = 40.0

SOIL_DEVICE_TOKEN = "IF7879-34D35A1"
SOIL_SIGNAL_TOKEN = "Hum-suolo_1"

IDS = {
    "ev": "prog001-SameEv1",
}


def now_ms():
    return int(time.time() * 1000)


def future_ms(minutes):
    return now_ms() + minutes * 60 * 1000


def headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }


def get_last_soil_value():
    page = 1

    while True:
        url = f"{SIGNALS_URL}?page={page}"
        r = requests.get(url, headers=headers(), timeout=30)
        r.raise_for_status()
        data = r.json()

        for item in data.get("data", []):
            if (
                item.get("device_token") == SOIL_DEVICE_TOKEN
                and item.get("signal_token") == SOIL_SIGNAL_TOKEN
            ):
                return item.get("last_recived_value")

        next_page = data.get("pages", {}).get("next")
        if not next_page:
            return None

        page = next_page


def push_signals(device, signals):
    payload = {"device": device, "signals": signals}
    r = requests.post(PUSH_URL, json=payload, headers=headers(), timeout=60)
    print("Push status:", r.status_code)
    print("Push response:", r.text)
    r.raise_for_status()


def main():
    soil_value = get_last_soil_value()

    if soil_value is None:
        print("Soil signal not found")
        return

    soil_value = float(soil_value)
    print("Last soil moisture value:", soil_value)

    if soil_value < THRESHOLD:
        print(f"Value below {THRESHOLD} -> irrigation")
        push_signals(
            IDS["ev"],
            [
                {"name": "start", "value": future_ms(3)},
                {"name": "duration", "value": 1},
            ],
        )
    else:
        print(f"Value >= {THRESHOLD} -> no irrigation")


if __name__ == "__main__":
    main()
