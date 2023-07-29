import json

import pytest
from src.Listings.GetPurchases import filter_out_claimed

data = {
    1: {
        'tickets': {
            1000: {
                'purchases': [
                    {
                        'claimed': True,
                    },
                    {
                        'claimed': True,
                    },
                    {
                        'claimed': False
                    }
                ]
            },
            1001: {
                'purchases': [
                    {
                        'claimed': True,
                    },
                    {
                        'claimed': True,
                    },
                    {
                        'claimed': True
                    }
                ]
            }
        }
    },
    2: {
        'tickets': {
            2000: {
                'purchases': [
                    {
                        'claimed': True,
                    },
                    {
                        'claimed': True,
                    },
                    {
                        'claimed': True,
                    }
                ]
            },
            2001: {
                'purchases': [
                    {
                        'claimed': True
                    }
                ]
            }
        }
    }
}

class TestGetPurchases:

    def test_filter_out_claimed(self):
        results = filter_out_claimed(data)

        assert len(results[1]['tickets'][1000]['purchases']) == 1
        assert len(results[1]['tickets']) == 1
        assert len(results) == 1

