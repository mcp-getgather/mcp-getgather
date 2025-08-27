import { Link } from "react-router";

export default function NotFound() {
  return (
    <div className="flex h-full w-full items-center justify-center p-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Page not found</h1>
        <p className="text-muted-foreground">
          The page you are looking for doesn’t exist.
        </p>
        <div className="space-x-4">
          <Link className="underline" to="/">
            Go to dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
