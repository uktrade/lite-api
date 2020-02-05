from goods.enums import PvGrading


def get_pv_grading_value_from_key(key: str):
    for k, v in PvGrading.choices:
        if key == k:
            return v
