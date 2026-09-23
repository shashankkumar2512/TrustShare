export default function SharedWithMeLoading() {
  return (
    <div className="shared-loading" aria-label="Loading shared files">
      <div className="shared-skeleton shared-skeleton-header" />
      <div className="shared-skeleton shared-skeleton-toolbar" />
      {[1, 2, 3, 4].map((item) => <div className="shared-skeleton shared-skeleton-row" key={item} />)}
    </div>
  );
}
