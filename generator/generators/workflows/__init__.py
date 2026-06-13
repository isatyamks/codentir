from generator.core.engine import SimulationEngine
from .story import _simulate_story
from .incident import _simulate_deep_incident_story


def generate_workflows(engine: SimulationEngine):
    num_stories = 20 * engine.config.scale_factor

    for i in range(num_stories):
        if i == 0:
            _simulate_deep_incident_story(engine, i)
        else:
            _simulate_story(engine, i)
