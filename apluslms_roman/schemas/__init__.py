from os.path import join
from apluslms_yamlidator.schemas import schema_registry
from .. import CACHE_DIR

schema_registry.register_module(__name__)
schema_registry.register_cache(join(CACHE_DIR, 'schemas'))
