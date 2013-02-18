import trap.ingredients as ingred
from trap.ingredients.common import TrapNode, node_run
import trap.recipes

class source_extraction(TrapNode):
    def trapstep(self, image_id, url,  parset):
        self.outputs['sources'] = ingred.source_extraction.extract_sources(url, parset)

        # we need to keep track of the image ID also, since we have no good
        # other way to identify the image otherwise
        self.outputs['image_id'] = image_id

node_run(__name__, source_extraction)

