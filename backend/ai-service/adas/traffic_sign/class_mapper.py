"""
TV1.2 - Class Mapper
Mapping 52 class từ YOLO model sang tên biển báo tiếng Việt không dấu
"""

from typing import Dict, Optional


class TrafficSignClassMapper:
    """
    Mapper cho 52 loại biển báo giao thông
    YOLO model được huấn luyện trên dataset có 52 class khác nhau
    """
    
    # Mapping class_id -> class_name (tiếng Việt không dấu)
    CLASS_MAPPING: Dict[int, str] = {
        # Biển báo cấm (1-10)
        0: "Cam di vao",
        1: "Cam di len",
        2: "Cam di nguoc chieu",
        3: "Cam re phai",
        4: "Cam re trai",
        5: "Cam vuot",
        6: "Cam dung va doi xe",
        7: "Cam dung",
        8: "Cam doi xe",
        9: "Cam bao hanh",
        10: "Cam thanh tra",
        
        # Biển báo hiệu lệnh (11-20)
        11: "Phai di len",
        12: "Phai re phai",
        13: "Phai re trai",
        14: "Phai di tien hoac re phai",
        15: "Phai di tien hoac re trai",
        16: "Di tien",
        17: "Re trai hoac tien",
        18: "Re phai hoac tien",
        19: "Phai vuot ben phai",
        20: "Phai vuot ben trai",
        
        # Biển báo thận trọng (21-35)
        21: "Nguon tro mat",
        22: "Duong giao thong khong bang chi dao",
        23: "Duong sat cap o ba",
        24: "Duong sat cap mot (A)",
        25: "Hiem nguy",
        26: "Pho di bo",
        27: "Duong ray xuong",
        28: "Hiem nguy",
        29: "Hiem nguy",
        30: "Hiem nguy",
        31: "Hiem nguy",
        32: "Duong hep ben phai",
        33: "Duong hep ben trai",
        34: "Duong hep hai ben",
        35: "Hiem nguy tro lai tuong lai",
        
        # Biển báo chỉ dẫn (36-40)
        36: "Gioi han toc do 20kmh",
        37: "Gioi han toc do 30kmh",
        38: "Gioi han toc do 50kmh",
        39: "Gioi han toc do 60kmh",
        40: "Gioi han toc do 80kmh",
        41: "Gioi han toc do 40kmh",
        42: "Gioi han toc do 100kmh",
        43: "Gioi han toc do 120kmh",
        44: "End of speed limit",
        45: "Khu vuc chuyen hoan",
        46: "Khu vuc chuyen hoan het",
        47: "Duong mot chieu",
        48: "Khu vuc do thi",
        49: "Ket thuc khu vuc do thi",
        50: "Priority road",
        51: "Ket thuc duong uu tien",
    }
    
    @classmethod
    def get_class_name(cls, class_id: int) -> Optional[str]:
        """
        Lấy tên biển báo từ class_id
        
        Args:
            class_id: Class ID từ YOLO (0-51)
        
        Returns:
            Class name (tiếng Việt không dấu) hoặc None nếu không tìm thấy
        """
        if class_id not in cls.CLASS_MAPPING:
            raise ValueError(f"Invalid class_id: {class_id}. Must be 0-51")
        return cls.CLASS_MAPPING.get(class_id)
    
    @classmethod
    def validate_class_id(cls, class_id: int) -> bool:
        """
        Kiểm tra class_id có hợp lệ không
        
        Args:
            class_id: Class ID cần kiểm tra
        
        Returns:
            True nếu hợp lệ, False nếu không
        """
        return 0 <= class_id <= 51 and class_id in cls.CLASS_MAPPING
    
    @classmethod
    def get_all_classes(cls) -> Dict[int, str]:
        """Lấy toàn bộ mapping"""
        return cls.CLASS_MAPPING.copy()
    
    @classmethod
    def get_class_info(cls, class_id: int) -> Dict:
        """
        Lấy thông tin chi tiết của class
        
        Returns:
            Dict với class_id, class_name
        """
        if not cls.validate_class_id(class_id):
            raise ValueError(f"Invalid class_id: {class_id}")
        
        return {
            'class_id': class_id,
            'class_name': cls.CLASS_MAPPING[class_id]
        }
