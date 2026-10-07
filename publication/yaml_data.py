"""Safe YAML loading through the available PyYAML implementation."""
import yaml
Loader=getattr(yaml,'CSafeLoader',yaml.SafeLoader)
def load(value):return yaml.load(value,Loader=Loader)
