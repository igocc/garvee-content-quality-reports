import { buildNewsroomBreadcrumb } from './newsroom-structured-data.mjs';

export default function NewsroomBreadcrumb({ homeUrl, pageUrl }) {
  const { itemListElement: items } = buildNewsroomBreadcrumb({ homeUrl, pageUrl });
  return (
    <nav aria-label="Breadcrumb">
      <ol className="newsroom-breadcrumb">
        {items.map((item, index) => (
          <li key={item.position}>
            {index === items.length - 1 ? (
              <span aria-current="page">{item.name}</span>
            ) : (
              <>
                <a href={item.item}>{item.name}</a>
                <span aria-hidden="true"> → </span>
              </>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
