#!/usr/bin/env python3
# River Sentinel - Autonomous Quadruped Security System

import json
import os

class Config:
    def __init__(self, profile_path="/home/hoke/river-sentinel/units/sentinel_profile.json"):
        self.profile_path = profile_path
        self.data = self.load_profile()

    def load_profile(self):
        if not os.path.exists(self.profile_path):
            print(f"Error: Profile not found at {self.profile_path}")
            return {}
        
        with open(self.profile_path, 'r') as f:
            return json.load(f)

    def get(self, key, default=None):
        keys = key.split('.')
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    @property
    def unit_id(self):
        return self.get('unit_id', 'UNKNOWN')

    @property
    def rth_enabled(self):
        return self.get('safety.rth_enabled', True)

config = Config()
