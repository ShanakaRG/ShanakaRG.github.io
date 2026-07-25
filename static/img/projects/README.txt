Project images. Suggested layout — one folder per project, matching the
project's "slug" in content/projects.yaml:

    projects/elephant/detection.png
    projects/tactile/hardware.png
    projects/tumour/segmentation.png

Then reference them in content/projects.yaml like this:

    images:
      - file: img/projects/elephant/detection.png
        alt: Short description for screen readers
        caption: Caption shown under the image
