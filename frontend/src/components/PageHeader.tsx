import { Badge } from "@/components/ui/badge";

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: {
    text: string;
    icon?: React.ComponentType<{ className?: string }>;
    variant?: "default" | "secondary" | "destructive" | "outline";
  };
}

export default function PageHeader({ title, description, badge }: PageHeaderProps) {
  return (
    <div className="mb-12 text-center">
      {badge && (
        <div className="mb-6 flex justify-center">
          <Badge
            variant={badge.variant || "secondary"}
            className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {badge.icon && <badge.icon className="mr-2 h-4 w-4" />}
            {badge.text}
          </Badge>
        </div>
      )}

      <h1 className="mb-4 text-3xl font-bold text-slate-900">{title}</h1>

      {description && <p className="mx-auto max-w-2xl text-lg text-gray-600">{description}</p>}
    </div>
  );
}
