import { useEffect, useMemo, useState } from "react";

type Brand = {
  id: string;
  name: string;
};

export default function Home() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [search, setSearch] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBrands = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URL(window.location.href).searchParams;
      const includeTest = Boolean(params.get("test"));
      const url = includeTest ? "/api/brands?test=1" : "/api/brands";
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Failed to load brands: ${res.status}`);
      const data = (await res.json()) as Brand[];
      setBrands(data);
    } catch (e) {
      console.error(e);
      setError("Error loading brands");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrands();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return brands;
    return brands.filter((b) => b.name.toLowerCase().includes(q));
  }, [brands, search]);

  const onImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const attempted = img.dataset.fallback;
    if (!attempted || attempted === "svg") {
      img.src = img.src.replace(/\.svg$/, ".png");
      img.dataset.fallback = "png";
    } else {
      img.src = "/__static/assets/logos/default.svg";
      img.onerror = null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="bg-white border-r w-80 p-8 flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <div className="text-2xl font-bold text-slate-800">GetGather</div>
            <div className="text-slate-500">Download your data!</div>
          </div>
          <input
            className="w-full rounded-lg border border-slate-200 bg-slate-100 px-4 py-3 text-slate-800 placeholder-slate-500 focus:outline-none"
            id="search"
            type="text"
            placeholder="Search brand"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <a
            href="https://github.com/mcp-getgather/mcp-getgather/blob/main/getgather/mcp/tools.md"
            target="_blank"
            rel="noreferrer"
            className="inline-block text-center bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2 rounded-md"
          >
            MCP Documentation
          </a>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8 overflow-x-auto">
          <div className="text-center text-slate-500 mb-6 text-xl">
            {loading
              ? "Loading..."
              : error
                ? error
                : `Available: ${filtered.length}`}
          </div>

          <div
            className="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7"
            data-testid="brands-grid"
          >
            {filtered.map((brand) => (
              <a
                key={brand.id}
                href={`/start/${brand.id}`}
                className="bg-white border rounded-xl shadow-sm flex flex-col items-center text-center p-5 hover:shadow-md hover:border-blue-600 transition"
                data-testid={`brand-card_${brand.id}`}
              >
                <img
                  className="w-12 h-12 object-contain mb-4 rounded-md bg-white"
                  src={`/__static/assets/logos/${brand.id}.svg`}
                  alt={brand.name}
                  onError={onImageError}
                  data-fallback="svg"
                />
                <div className="text-slate-800 text-base text-xl font-medium mb-1">
                  {brand.name}
                </div>
              </a>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
