from dataclasses import dataclass
from itertools import combinations
from math import sqrt

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError


FEATURE_SIZE = 64
HASH_SIZE = 8
GRID_SIZE = 8


@dataclass(frozen=True)
class PhotoMatchResult:
    old_photo: object
    new_photo: object
    score: float
    visual_similarity: float
    temporal_score: float
    azimuth_score: float
    candidates_analyzed: int

    @property
    def quality_label(self):
        if self.score >= 82:
            return 'excellent'
        if self.score >= 68:
            return 'good'
        if self.score >= 52:
            return 'acceptable'
        return 'fallback'


@dataclass(frozen=True)
class ImageFeatures:
    average_hash: tuple
    difference_hash: tuple
    luminance_grid: tuple
    edge_grid: tuple
    color_histogram: tuple
    brightness: float
    contrast: float
    aspect_ratio: float


def find_best_comparison_pair(photos):
    """Find the best old/new photo pair by visual similarity and metadata.

    The algorithm extracts compact computer-vision descriptors from each image
    and evaluates every pair. It prefers visually similar perspective and scene
    structure, while still rewarding historical distance and close azimuth.
    """

    photos = [photo for photo in photos if getattr(photo, 'year', None) is not None]
    if len(photos) < 2:
        return None

    features_by_id = {}
    for photo in photos:
        features_by_id[photo.id] = extract_image_features(photo)

    best = None
    candidates_analyzed = 0

    for first, second in combinations(photos, 2):
        old_photo, new_photo = sorted((first, second), key=lambda item: (item.year, item.id))
        if old_photo.year == new_photo.year:
            continue

        candidates_analyzed += 1
        visual_similarity = compare_visual_features(
            features_by_id.get(old_photo.id),
            features_by_id.get(new_photo.id),
        )
        temporal_score = compare_years(old_photo.year, new_photo.year)
        azimuth_score = compare_azimuths(old_photo.azimuth, new_photo.azimuth)

        score = (
            visual_similarity * 0.74
            + temporal_score * 0.16
            + azimuth_score * 0.10
        )

        if best is None or score > best.score:
            best = PhotoMatchResult(
                old_photo=old_photo,
                new_photo=new_photo,
                score=round(score, 2),
                visual_similarity=round(visual_similarity, 2),
                temporal_score=round(temporal_score, 2),
                azimuth_score=round(azimuth_score, 2),
                candidates_analyzed=candidates_analyzed,
            )

    if best:
        return PhotoMatchResult(
            old_photo=best.old_photo,
            new_photo=best.new_photo,
            score=best.score,
            visual_similarity=best.visual_similarity,
            temporal_score=best.temporal_score,
            azimuth_score=best.azimuth_score,
            candidates_analyzed=candidates_analyzed,
        )

    return chronological_fallback(photos)


def extract_image_features(photo):
    try:
        with Image.open(photo.image) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            return build_features(image)
    except (OSError, ValueError, UnidentifiedImageError):
        return None


def build_features(image):
    aspect_ratio = image.width / image.height if image.height else 1.0
    small_rgb = ImageOps.fit(image, (FEATURE_SIZE, FEATURE_SIZE), method=Image.Resampling.LANCZOS)
    small_gray = small_rgb.convert('L')
    edges = small_gray.filter(ImageFilter.FIND_EDGES)

    average_hash = make_average_hash(small_gray)
    difference_hash = make_difference_hash(small_gray)
    luminance_grid = make_grid(small_gray, GRID_SIZE)
    edge_grid = make_grid(edges, GRID_SIZE)
    color_histogram = make_color_histogram(small_rgb)

    pixels = list(small_gray.getdata())
    brightness = sum(pixels) / (255 * len(pixels))
    variance = sum((pixel / 255 - brightness) ** 2 for pixel in pixels) / len(pixels)

    return ImageFeatures(
        average_hash=average_hash,
        difference_hash=difference_hash,
        luminance_grid=luminance_grid,
        edge_grid=edge_grid,
        color_histogram=color_histogram,
        brightness=brightness,
        contrast=sqrt(variance),
        aspect_ratio=aspect_ratio,
    )


def make_average_hash(gray_image):
    thumb = gray_image.resize((HASH_SIZE, HASH_SIZE), Image.Resampling.LANCZOS)
    pixels = list(thumb.getdata())
    avg = sum(pixels) / len(pixels)
    return tuple(1 if pixel >= avg else 0 for pixel in pixels)


def make_difference_hash(gray_image):
    thumb = gray_image.resize((HASH_SIZE + 1, HASH_SIZE), Image.Resampling.LANCZOS)
    bits = []
    for y in range(HASH_SIZE):
        for x in range(HASH_SIZE):
            bits.append(1 if thumb.getpixel((x, y)) > thumb.getpixel((x + 1, y)) else 0)
    return tuple(bits)


def make_grid(gray_image, grid_size):
    resized = gray_image.resize((grid_size, grid_size), Image.Resampling.BILINEAR)
    return tuple(pixel / 255 for pixel in resized.getdata())


def make_color_histogram(rgb_image):
    bins_per_channel = 8
    histogram = []
    for channel in rgb_image.split():
        channel_hist = channel.histogram()
        step = 256 // bins_per_channel
        total = max(1, sum(channel_hist))
        histogram.extend(
            sum(channel_hist[index:index + step]) / total
            for index in range(0, 256, step)
        )
    return tuple(histogram)


def compare_visual_features(old_features, new_features):
    if old_features is None or new_features is None:
        return 35.0

    hash_score = 100 * (1 - hamming_distance(old_features.average_hash, new_features.average_hash))
    dhash_score = 100 * (1 - hamming_distance(old_features.difference_hash, new_features.difference_hash))
    luminance_score = vector_similarity(old_features.luminance_grid, new_features.luminance_grid)
    edge_score = vector_similarity(old_features.edge_grid, new_features.edge_grid)
    color_score = histogram_intersection(old_features.color_histogram, new_features.color_histogram)
    brightness_score = 100 * (1 - min(1, abs(old_features.brightness - new_features.brightness)))
    contrast_score = 100 * (1 - min(1, abs(old_features.contrast - new_features.contrast) * 2))
    aspect_score = 100 * (1 - min(1, abs(old_features.aspect_ratio - new_features.aspect_ratio) / 1.5))

    return (
        hash_score * 0.17
        + dhash_score * 0.16
        + luminance_score * 0.20
        + edge_score * 0.20
        + color_score * 0.12
        + brightness_score * 0.05
        + contrast_score * 0.05
        + aspect_score * 0.05
    )


def hamming_distance(first, second):
    if not first or not second or len(first) != len(second):
        return 1
    return sum(a != b for a, b in zip(first, second)) / len(first)


def vector_similarity(first, second):
    if not first or not second or len(first) != len(second):
        return 0
    distance = sqrt(sum((a - b) ** 2 for a, b in zip(first, second)) / len(first))
    return 100 * (1 - min(1, distance))


def histogram_intersection(first, second):
    if not first or not second or len(first) != len(second):
        return 0
    return 100 * sum(min(a, b) for a, b in zip(first, second)) / 3


def compare_years(old_year, new_year):
    return 100 * min(1, max(0, new_year - old_year) / 80)


def compare_azimuths(old_azimuth, new_azimuth):
    if old_azimuth is None or new_azimuth is None:
        return 65
    diff = abs(old_azimuth - new_azimuth) % 360
    diff = min(diff, 360 - diff)
    return 100 * (1 - min(1, diff / 90))


def chronological_fallback(photos):
    sorted_photos = sorted(photos, key=lambda item: (item.year, item.id))
    old_photo = sorted_photos[0]
    new_photo = sorted_photos[-1]
    return PhotoMatchResult(
        old_photo=old_photo,
        new_photo=new_photo,
        score=25.0,
        visual_similarity=0.0,
        temporal_score=compare_years(old_photo.year, new_photo.year),
        azimuth_score=compare_azimuths(old_photo.azimuth, new_photo.azimuth),
        candidates_analyzed=1,
    )
