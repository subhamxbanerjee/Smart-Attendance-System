from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def debug_build_encodings(request):
    """Debug view to force build encodings and show result"""
    try:
        from .encodings import build_encodings, save_encodings
        from django.conf import settings
        
        print(f"DEBUG: Building from {settings.MEDIA_ROOT}")
        encs, count = build_encodings(settings.MEDIA_ROOT)
        result = {
            "status": "success",
            "count_images_processed": count,
            "usns_found": list(encs.keys()),
            "media_root": str(settings.MEDIA_ROOT)
        }
        return Response(result)
    except Exception as e:
        import traceback
        return Response({"status": "error", "error": str(e), "trace": traceback.format_exc()})
