# Palette's Journal

## 2024-05-23 - Micro-interactions in Desktop Apps
**Learning:** Users often expect web-like interactions (Drag & Drop) even in desktop toolkits like Qt, where they aren't enabled by default. "Broken promises" (help text saying one thing, code doing another) destroy trust faster than missing features.
**Action:** Implemented `dragEnterEvent` and `dropEvent` across key tabs to match user expectations.

## 2024-05-23 - Vertical Layouts for Tools
**Learning:** Moving from Landscape to Portrait (Phone-on-Desktop) shifts the hierarchy. Vertical space becomes expensive. Queues/Lists often need to be collapsible or secondary to the primary "Preview/Action" area.
**Action:** Adopted a "Preview First" vertical layout with a "Hold to Compare" interaction to save space compared to side-by-side views.
