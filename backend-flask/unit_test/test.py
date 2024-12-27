import unittest #pragma: no cover
import coverage #pragma: no cover
import cv2

class TestUtilMethods(unittest.TestCase):
    def test_upload_gsi(self):
        from app.controller.facial_service.utils import upload_image_to_gsi
        img_test = cv2.imread('./unit_test/img.jpeg')
        link_face_1 = upload_image_to_gsi(img=img_test)
        link_face_2 = upload_image_to_gsi(file=cv2.imencode('.png', img_test)[1].tobytes())
        print('url = ', link_face_1)
        print('url = ', link_face_2)

    
if __name__ == '__main__':
    cov = coverage.Coverage()
    cov.start()
    try:
        unittest.main(verbosity=2)
    except:  # catch-all except clause
        pass
    cov.stop()
    cov.save()
    cov.xml_report()
    print("Done.")