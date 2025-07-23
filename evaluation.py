#evaluate the doodle agent

import os
import json
import numpy as np
from PIL import Image
from evaluation_metrics_lite import DoodleEvaluatorLite

#evaluate based on color harmony

def evaluate_color_harmony(doodle_path: str):
    doodle = Image.open(doodle_path)
    doodle_array = np.array(doodle)
    evaluator = DoodleEvaluatorLite()
    metrics = evaluator.evaluate_doodle(doodle_path)
    return metrics['color_harmony']


        