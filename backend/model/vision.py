from google.cloud import vision
from backend.model.location import Location
import json
from backend.utils.vision_utils import load_image_from_path, load_image_from_base64, web_detection_to_dict

class VisionProcessor:
    _client = None
    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = vision.ImageAnnotatorClient()
        return cls._client
    def annotate(self, path: str) -> vision.WebDetection:
        if path.startswith("http") or path.startswith("gs:"):
            image = vision.Image()
            image.source.image_uri = path
        elif path.startswith("data"):
            image_data = load_image_from_base64(path)
            image = vision.Image({"content": image_data})
        else:
            image_data = load_image_from_path(path)
            image = vision.Image({"content": image_data})
        client = self.get_client()
        web_detection = client.web_detection(image=image).web_detection
        return web_detection

    def report(self, path: str) -> str:
        """Prints detected features in the provided web annotations.
        Args:
            path: 이미지 파일의 경로를 전달
        """
        annotations = self.annotate(path)
        if annotations.pages_with_matching_images:
            print(
                f"\n{len(annotations.pages_with_matching_images)} Pages with matching images retrieved"
            )
            for page in annotations.pages_with_matching_images:
                print(f"Url   : {page.url}")

        if annotations.partial_matching_images:
            print(f"\n{len(annotations.partial_matching_images)} Partial Matches found: ")
            for image in annotations.partial_matching_images:
                print(f"Url  : {image.url}")

        if annotations.web_entities:
            print(f"\n{len(annotations.web_entities)} Web entities found: ")
            for entity in annotations.web_entities:
                print(f"Score      : {entity.score}")
                print(f"Description: {entity.description}")

        annotations_dict = web_detection_to_dict(annotations)

        with open('annotations.json', 'w', encoding='utf-8') as f:
            json.dump(annotations_dict, f, ensure_ascii=False, indent=4)
        return Location(
            url=annotations_dict['urls'][0],
            image_url=annotations_dict['images'][0],
            entity=annotations_dict['entities']
        ).json()

if __name__ == "__main__":
    processor = VisionProcessor()
    filepath = "/Users/everyshare/PycharmProjects/herobot/backend/datas/test2.jpg"
    location = processor.report(filepath)
    print(location)
