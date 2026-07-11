from app.core.pixelseal import model
from app.services.image_service import ImageService


class EmbedService:

    @staticmethod
    def embed(
        input_path,
        output_path,
        message,
    ):

        image = ImageService.load_image(input_path)

        result = model.embed(
            imgs=image,
            msgs=message,
            is_video=False,
        )

        ImageService.save_image(
            result["imgs_w"],
            output_path,
        )

        return result