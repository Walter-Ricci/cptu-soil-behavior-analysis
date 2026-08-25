"""Input preparation for the Premstaller CPTu dataset."""
from __future__ import annotations

import pandas as pd

USECOLS = ["ID", "test_type", "basin_valley", "Depth (m)", "qc (MPa)", "fs (kPa)",
           "u2 (kPa)", "qt (MPa)", "σ,v (kPa)", "σ',v (kPa)", "Qtn (-)", "Fr (%)", "Ic (-)"]
RENAME = {"Depth (m)": "depth", "qc (MPa)": "qc", "fs (kPa)": "fs", "u2 (kPa)": "u2",
          "qt (MPa)": "qt", "σ,v (kPa)": "sigma_v", "σ',v (kPa)": "sigma_eff",
          "Qtn (-)": "qtn_published", "Fr (%)": "fr_published", "Ic (-)": "ic_published"}


def load_profiles(path, max_profiles=10, selected_id=None, chunksize=200_000):
    """Load CPTu/SCPTu records while preserving profile order in the source."""
    parts, selected = [], []
    for chunk in pd.read_csv(path, usecols=USECOLS, chunksize=chunksize, low_memory=False):
        chunk = chunk[chunk.test_type.isin(["CPTu", "SCPTu"])]
        if selected_id is not None:
            chunk = chunk[pd.to_numeric(chunk.ID, errors="coerce").eq(selected_id)]
        else:
            for value in chunk.ID.drop_duplicates():
                if value not in selected and len(selected) < max_profiles:
                    selected.append(value)
            chunk = chunk[chunk.ID.isin(selected)]
        if not chunk.empty:
            parts.append(chunk)
    if not parts:
        raise ValueError("No CPTu/SCPTu profiles found.")
    data = pd.concat(parts, ignore_index=True).rename(columns=RENAME)
    numeric = list(RENAME.values())
    data[numeric] = data[numeric].apply(pd.to_numeric, errors="coerce")
    return data


def prepare_profile(frame):
    required = ["depth", "qc", "fs", "u2", "qt", "sigma_v", "sigma_eff"]
    out = frame.dropna(subset=required).sort_values("depth").drop_duplicates("depth", keep="last")
    if len(out) < 10:
        raise ValueError("Profile has fewer than 10 complete measurements.")
    return out.reset_index(drop=True)
