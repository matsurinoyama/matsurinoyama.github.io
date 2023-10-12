import { error } from "@sveltejs/kit";
import { works } from "../data.js";

export function load({ params }) {
  const work = works.find((work) => work.slug === params.slug);

  if (!work) throw error(404);

  return {
    work,
  };
}
