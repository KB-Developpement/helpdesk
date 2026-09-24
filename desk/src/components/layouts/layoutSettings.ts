import LucideBookOpen from "~icons/lucide/book-open";
import LucideContact2 from "~icons/lucide/contact-2";
import LucideTicket from "~icons/lucide/ticket";
import LucideLayoutDashboard from "~icons/lucide/layout-dashboard";
import { OrganizationsIcon } from "../icons";
import PhoneIcon from "../icons/PhoneIcon.vue";
import LucideHome from "~icons/lucide/home";
import LucideCoins from "~icons/lucide/coins";
import { __ } from "@/translation";

export const agentPortalSidebarOptions = [
  {
    label: __("Home"),
    icon: LucideHome,
    to: "Home",
  },
  {
    label: __("Dashboard"),
    icon: LucideLayoutDashboard,
    to: "Dashboard"
  },
  {
    label: __("Tickets"),
    icon: LucideTicket,
    to: "TicketsAgent",
  },
  {
    label: __("Knowledge Base"),
    icon: LucideBookOpen,
    to: "AgentKnowledgeBase",
  },
  {
    label: __("Customers"),
    icon: OrganizationsIcon,
    to: "CustomerList",
  },
  {
    label: __("Contacts"),
    icon: LucideContact2,
    to: "ContactList",
  },
  {
    label: __("Call Logs"),
    icon: PhoneIcon,
    to: "CallLogs",
  },
  // kb_credits — manuel support §7 « Menu → Crédits d'intervention ».
  // Getter: the label is translated when rendered, not at module load
  // (translations may not be fetched yet at that point).
  {
    get label() {
      return __("Intervention credits");
    },
    icon: LucideCoins,
    to: "KBCreditsDashboard",
  },
];

export const customerPortalSidebarOptions = [
  {
    label: __("Tickets"),
    icon: LucideTicket,
    to: "TicketsCustomer",
  },
  // kb_credits — manuel client §7 « Tickets → Mes crédits »
  {
    get label() {
      return __("My credits");
    },
    icon: LucideCoins,
    to: "CustomerCredits",
  },
  {
    label: __("Knowledge Base"),
    icon: LucideBookOpen,
    to: "CustomerKnowledgeBase",
  },
];
