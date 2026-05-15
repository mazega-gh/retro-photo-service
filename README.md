# RetroPhoto Service

Web service for georeferenced archive photos with an interactive Leaflet map,
moderation workflow, role-based access, and a "then and now" comparison view.

## Main Features

- Interactive map centered on Yaroslavl.
- Location storage with PostGIS `PointField` coordinates.
- Archive photo upload with year, description, location, and optional azimuth.
- Public API exposes only published photos.
- Intelligent "then and now" pair selection for the comparison slider.
- Moderation queue for approving and rejecting user uploads.
- Admin panel for users, roles, locations, photos, statuses, and logs.
- Leaflet marker clustering for dense location areas.
- OpenAPI schema and Swagger/Redoc documentation.

## Tech Stack

- Python, Django, Django REST Framework
- PostgreSQL with PostGIS
- GeoDjango and `djangorestframework-gis`
- Leaflet and Leaflet.markercluster
- Pillow for image handling
- drf-spectacular for API documentation

## Intelligent Photo Matching

The comparison slider does not simply take the oldest and newest photos anymore.
For a selected location the backend analyzes every published photo pair and
selects the strongest old/new match.

Endpoint:

```http
GET /api/photos/smart-compare/?location=<location_id>
```

The algorithm extracts compact visual descriptors with Pillow:

- perceptual average hash and difference hash;
- luminance grid for composition similarity;
- edge grid for perspective and object contours;
- RGB color histogram;
- aspect ratio, brightness, and contrast;
- metadata signals: year distance and shooting azimuth.

Each candidate pair receives a weighted score. The frontend shows the selected
pair in the existing slider and displays the AI score, number of analyzed pairs,
visual similarity, and azimuth score. If analysis is unavailable, the interface
falls back to a chronological pair so the user always gets a comparison.

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables or `.env`:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
```

4. Make sure PostgreSQL/PostGIS and GDAL paths in `config/settings.py` match your machine.
5. Apply migrations:

```powershell
python manage.py migrate
```

6. Create a superuser:

```powershell
python manage.py createsuperuser
```

7. Run the development server:

```powershell
python manage.py runserver
```

## Important URLs

- Main map: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`
- Custom admin panel: `http://127.0.0.1:8000/admin-panel/`
- Moderation panel: `http://127.0.0.1:8000/moderation/`
- API docs: `http://127.0.0.1:8000/api/docs/`
- API schema: `http://127.0.0.1:8000/api/schema/`
- Redoc: `http://127.0.0.1:8000/api/redoc/`

## Seeded Reference Data

Migrations create the base roles and moderation statuses:

- Roles: `user`, `moderator`, `admin`
- Statuses: `На проверке`, `Опубликовано`, `Отклонено`

## Tests

Run:

```powershell
python manage.py test
```

The test suite covers registration, photo upload validation, public visibility,
and moderation permissions.

## Production Notes

Before deployment:

- Set `DJANGO_DEBUG=False`.
- Set a real `DJANGO_SECRET_KEY`.
- Configure `DJANGO_ALLOWED_HOSTS`.
- Enable HTTPS and secure cookie flags:
  - `DJANGO_SECURE_SSL_REDIRECT=True`
  - `DJANGO_SESSION_COOKIE_SECURE=True`
  - `DJANGO_CSRF_COOKIE_SECURE=True`
- Serve static and media files through Nginx or another web server.

## Recommended Next Improvements

- Generate WebP thumbnails during upload.
- Add map bounding-box filtering for large datasets.
- Add request throttling for authentication and uploads.
- Add service worker caching if offline mode remains in the diploma text.
- Normalize all Russian UI strings to UTF-8 where mojibake is still visible.
