import {
  Facebook,
  Instagram,
  Twitter,
  Linkedin,
} from "lucide-react";

export const SOCIAL_PLATFORMS = [
  {
    id: "facebook",
    label: "Facebook",
    description: "Connect pages and groups to publish posts and gather insights.",
    icon: Facebook,
    badgeClass: "border-blue-200 bg-blue-50 text-blue-700",
  },
  {
    id: "instagram",
    label: "Instagram",
    description: "Enable posting to business profiles and track engagement metrics.",
    icon: Instagram,
    badgeClass: "border-pink-200 bg-pink-50 text-pink-700",
  },
  {
    id: "twitter",
    label: "Twitter / X",
    description: "Publish to X and monitor tweet performance automatically.",
    icon: Twitter,
    badgeClass: "border-slate-200 bg-slate-50 text-slate-700",
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    description: "Share to company pages and sync professional analytics.",
    icon: Linkedin,
    badgeClass: "border-sky-200 bg-sky-50 text-sky-700",
  },
];

export const getPlatformLabel = (platformId) => {
  const platform = SOCIAL_PLATFORMS.find((item) => item.id === platformId);
  return platform ? platform.label : platformId;
};
