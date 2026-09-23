// client/src/features/analytics/config/iconRegistry.js

import {
  HardDrive,
  Upload,
  Download,
  Share2,
  Trash2,
  ShieldCheck,
  AlertCircle,
  ShieldOff,
  ShieldAlert,
  Eye,
  MapPin,
  Inbox,
} from "lucide-react";

export const ICON_REGISTRY = {
  HardDrive,
  Upload,
  Download,
  Share2,
  Trash2,
  ShieldCheck,
  AlertCircle,
  ShieldOff,
  ShieldAlert,
  Eye,
  MapPin,
  Inbox,
};

export function getIcon(name) {
  return ICON_REGISTRY[name] || null;
}