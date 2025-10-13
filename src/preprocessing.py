from scipy.ndimage import median_filter, binary_opening, binary_closing
from skimage import color, filters


def preprocess_image(img, filter_size=3, threshold=None):
    """
    Basic preprocessing pipeline for keyboard (or similar) images.

    Steps:
    1. Convert RGB image to grayscale.
    2. Apply median filtering to reduce noise.
    3. Compute a binary mask (automatic Otsu thresholding or manual threshold).
    4. Apply morphological opening (remove small spots) and closing (fill small holes).

    Parameters:
    ----------
    img : ndarray
        Input RGB image.
    filter_size : int, optional
        Size of the median filter (default=3).
    threshold : float or None, optional
        Manual threshold (0–1 range). If None, Otsu’s method is used.

    Returns:
    -------
    cleaned : ndarray (bool)
        Binary (True/False) image ready for further analysis.
    """
    # Step 1: Convert to grayscale
    gray = color.rgb2gray(img)

    # Step 2: Reduce noise with a median filter
    filtered = median_filter(gray, size=filter_size)

    # Step 3: Binarize using Otsu’s threshold (automatic) or manual threshold
    if threshold is None:
        threshold = filters.threshold_otsu(filtered)
    binary = (
        filtered < threshold
    )  # keys/touches usually darker → invert logic if needed

    # Step 4: Morphological cleaning — remove noise, fill gaps
    cleaned = binary_closing(binary_opening(binary))

    return cleaned
