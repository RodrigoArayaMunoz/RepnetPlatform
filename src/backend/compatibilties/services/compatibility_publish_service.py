from services.mercadolibre_vehicle_service import MercadoLibreVehicleService


class CompatibilityPublishService:
    def __init__(self):
        self.meli_service = MercadoLibreVehicleService()

    def publish_candidate(self, item_id: str, product_id: str):
        return self.meli_service.add_compatibility(item_id=item_id, product_id=product_id)