"""
Wagtail models for the portfolio.

Page tree (created once in the admin, then you only add children):

  Home                      HomePage              /
  ├── Projects              ProjectIndexPage      /projects/
  │   └── Sensor node       ProjectPage           /projects/sensor-node/
  └── Writing               WritingIndexPage      /writing/
      └── Why an RTOS       WritingPage           /writing/why-an-rtos/

Projects and writings are different page types, so they stay grouped by
category even though everything lives in the same SQLite database.

Written for Wagtail 6.x / 7.x (StreamField needs no use_json_field flag).
Needs "taggit" and "modelcluster" in INSTALLED_APPS (Wagtail installs both).
"""
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtail.search import index


PAGE_SIZE = 10  # items per page on /projects/ and /writing/


# ───────────────────────── shared article body ─────────────────────────
class CodeBlock(blocks.StructBlock):
    language = blocks.CharBlock(required=False, help_text="e.g. c, python, bash")
    code = blocks.TextBlock()

    class Meta:
        icon = "code"
        label = "Code"


class ArticleBody(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="title", icon="title")
    paragraph = blocks.RichTextBlock(
        features=["bold", "italic", "link", "ol", "ul", "blockquote"],
        icon="pilcrow",
    )
    image = ImageChooserBlock(icon="image")
    code = CodeBlock()


class SiblingNavMixin:
    """Adds `previous_page` / `next_page` (within the same category) to the template context."""

    sibling_ordering = ("-first_published_at",)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        siblings = list(
            type(self).objects.sibling_of(self).live().order_by(*self.sibling_ordering)
        )
        ids = [p.pk for p in siblings]
        i = ids.index(self.pk) if self.pk in ids else None
        context["previous_page"] = siblings[i - 1] if i not in (None, 0) else None
        context["next_page"] = siblings[i + 1] if i is not None and i + 1 < len(siblings) else None
        return context


# ───────────────────────────── home ─────────────────────────────
class HomePage(Page):
    """Static content (name, stats, bio, socials) stays in the template.
    This page only pulls the latest CMS items for the home previews."""

    max_count = 1
    template = "home_page.html"
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["app.ProjectIndexPage", "app.WritingIndexPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["latest_projects"] = ProjectPage.objects.live().order_by(
            "-year", "-first_published_at"
        )[:2]
        context["latest_writings"] = WritingPage.objects.live().order_by(
            "-date", "-first_published_at"
        )[:2]
        context["project_index"] = ProjectIndexPage.objects.live().first()
        context["writing_index"] = WritingIndexPage.objects.live().first()
        return context


# ─────────────────────────── projects ───────────────────────────
class ProjectIndexPage(Page):
    """/projects/ : lists every ProjectPage underneath it."""

    max_count = 1
    intro = models.CharField(max_length=200, blank=True)
    template = "project_index_page.html"
    parent_page_types = ["app.HomePage"]
    subpage_types = ["app.ProjectPage"]
    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        qs = ProjectPage.objects.child_of(self).live().order_by("-year", "-first_published_at")
        context["projects"] = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
        return context


class ProjectPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "app.ProjectPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class ProjectLink(Orderable):
    page = ParentalKey("app.ProjectPage", related_name="links", on_delete=models.CASCADE)
    label = models.CharField(max_length=60, help_text="e.g. Source code")
    url = models.URLField()
    panels = [FieldPanel("label"), FieldPanel("url")]


class ProjectPage(SiblingNavMixin, Page):
    role = models.CharField(max_length=60, help_text="e.g. Founder, Side project")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    summary = models.TextField(max_length=300, help_text="Shown on cards and lists.")
    tags = ClusterTaggableManager(through=ProjectPageTag, blank=True)
    body = StreamField(ArticleBody(), blank=True)

    template = "project_page.html"
    parent_page_types = ["app.ProjectIndexPage"]
    subpage_types = []
    sibling_ordering = ("-year", "-first_published_at")

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [FieldPanel("role"), FieldPanel("year"), FieldPanel("tags")], heading="Details"
        ),
        FieldPanel("summary"),
        FieldPanel("body"),
        InlinePanel("links", label="Links"),
    ]
    search_fields = Page.search_fields + [
        index.SearchField("summary"),
        index.SearchField("body"),
    ]


# ─────────────────────────── writings ───────────────────────────
class WritingIndexPage(Page):
    """/writing/ : lists every WritingPage underneath it."""

    max_count = 1
    intro = models.CharField(max_length=200, blank=True)
    template = "writing_index_page.html"
    parent_page_types = ["app.HomePage"]
    subpage_types = ["app.WritingPage"]
    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        qs = WritingPage.objects.child_of(self).live().order_by("-date", "-first_published_at")
        context["writings"] = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
        return context


class WritingPage(SiblingNavMixin, Page):
    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=40, blank=True, help_text="e.g. Notes, Learning")
    excerpt = models.TextField(max_length=300, help_text="Shown on cards and lists.")
    body = StreamField(ArticleBody(), blank=True)

    template = "writing_page.html"
    parent_page_types = ["app.WritingIndexPage"]
    subpage_types = []
    sibling_ordering = ("-date", "-first_published_at")

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("date"), FieldPanel("category")], heading="Details"),
        FieldPanel("excerpt"),
        FieldPanel("body"),
    ]
    search_fields = Page.search_fields + [
        index.SearchField("excerpt"),
        index.SearchField("body"),
    ]
