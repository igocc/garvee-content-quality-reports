import {
  buildNewsroomJsonLd,
  serializeJsonLd,
} from './newsroom-structured-data.mjs';

export default function NewsroomJsonLd(props) {
  const jsonLd = buildNewsroomJsonLd(props);
  return (
    <script
      id="newsroom-jsonld"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: serializeJsonLd(jsonLd) }}
    />
  );
}
