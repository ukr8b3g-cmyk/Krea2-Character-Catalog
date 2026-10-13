from .nodes import Krea2CatalogPromptFile

NODE_CLASS_MAPPINGS = {"Krea2CatalogPromptFile": Krea2CatalogPromptFile}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2CatalogPromptFile": "Krea2 Catalog · File Prompt"}
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
