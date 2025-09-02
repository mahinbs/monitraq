import torch, torchvision, PIL, cv2, pydicom, pandas, skimage
print("torch", torch.__version__, "cuda:", torch.cuda.is_available())
print("torchvision", torchvision.__version__)
print("Pillow", PIL.__version__)
print("opencv", getattr(cv2, "__version__", "n/a"))
print("pandas", pandas.__version__)
print("skimage", skimage.__version__)
print("OK ✅")
