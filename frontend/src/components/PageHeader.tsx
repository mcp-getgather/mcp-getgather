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

export default function PageHeader({
  title,
  description,
  badge,
}: PageHeaderProps) {
  return (
    <div className="text-center mb-12">
      {badge && (
        <div className="flex justify-center mb-6">
          <Badge
            variant={badge.variant || "secondary"}
            className="bg-indigo-600 text-white hover:bg-indigo-700 px-4 py-2 text-sm font-medium rounded-full"
          >
            {badge.icon && <badge.icon className="w-4 h-4 mr-2" />}
            {badge.text}
          </Badge>
        </div>
      )}

      <h1 className="text-3xl font-bold text-slate-900 mb-4">{title}</h1>

      {description && (
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">{description}</p>
      )}
    </div>
  );
}
