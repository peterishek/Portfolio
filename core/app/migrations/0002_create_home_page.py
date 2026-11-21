from django.db import migrations


def create_homepage(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    HomePage = apps.get_model("app.HomePage")

    # Skip if a HomePage already exists (e.g. your local database)
    if HomePage.objects.exists():
        return

    # Remove Wagtail's default welcome page (and its localhost Site)
    Page.objects.filter(id=2).delete()

    content_type, _ = ContentType.objects.get_or_create(
        model="homepage", app_label="app"
    )

    homepage = HomePage.objects.create(
        title="Home",
        draft_title="Home",
        slug="home",
        content_type=content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
    )

    Site.objects.create(
        hostname="portfolio-env.eba-fhjz3r6u.eu-north-1.elasticbeanstalk.com",
        root_page=homepage,
        is_default_site=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
        ("wagtailcore", "0052_pagelogentry"),
    ]

    operations = [
        migrations.RunPython(create_homepage, migrations.RunPython.noop),
    ]