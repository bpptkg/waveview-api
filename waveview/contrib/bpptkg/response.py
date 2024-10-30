from obspy import Inventory as ObspyInventory
from obspy import Stream, read_inventory

from waveview.inventory.models import Inventory


def remove_instrument_response(inventory: Inventory, st: Stream) -> Stream:
    for inv_file in inventory.files.all():
        inv: ObspyInventory = read_inventory(inv_file.file)
        try:
            st.merge(fill_value=0)
            st.detrend("demean")
            pre_filt = [0.001, 0.005, 45, 50]
            st.remove_response(
                inventory=inv, pre_filt=pre_filt, output="DISP", water_level=60
            )
            return st
        except Exception:
            pass
    raise Exception("No matching inventory found.")
