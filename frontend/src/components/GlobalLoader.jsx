import { useIsFetching } from "@tanstack/react-query";

const GlobalLoader = () => {
  const isFetching = useIsFetching();

  if (!isFetching) return null;

  return (
    <div className="global-loading-bar">
      <div className="global-loading-bar__progress" style={{ width: "100%" }} />
    </div>
  );
};

export default GlobalLoader;
