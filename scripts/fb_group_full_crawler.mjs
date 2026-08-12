import fs from "node:fs";

const groupId = "186097664924714";
const topArticleSelector = `[role="dialog"] [role="article"]:has(h3 a[href*="/groups/${groupId}"])`;

async function extractPost(tab, post) {
  return tab.playwright.evaluate((args) => {
    const top = document.querySelector(args.topArticleSelector);
    if (!top) return null;
    const commentNodes = Array.from(top.querySelectorAll('[role="article"]'));
    const imagesFrom = (root) => Array.from(root.querySelectorAll("img")).map((image) => {
      const link = image.closest("a")?.href || "";
      return {
        alt: image.getAttribute("alt") || "",
        src: image.getAttribute("src") || "",
        width: Number(image.getAttribute("width") || image.clientWidth || image.naturalWidth || 0),
        height: Number(image.getAttribute("height") || image.clientHeight || image.naturalHeight || 0),
        photo_url: link,
      };
    }).filter((image) => image.src.startsWith("http")
      && (image.photo_url.includes("/photo") || image.photo_url.includes("/events/"))
      && (image.width >= 100 || image.height >= 100));

    const comments = commentNodes.map((comment, index) => {
      const links = Array.from(comment.querySelectorAll("a"));
      const dateLink = links.find((link) => String(link.href).includes("comment_id="));
      const href = dateLink?.href || "";
      const replyMatch = href.match(/[?&]reply_comment_id=([0-9]+)/);
      const commentMatch = href.match(/[?&]comment_id=([0-9]+)/);
      const authorLink = links.find((link) => (String(link.href).includes("/user/") || String(link.href).includes("profile.php")) && (link.innerText || "").trim());
      let rawText = comment.innerText.trim();
      const nestedTexts = Array.from(comment.querySelectorAll('[role="article"]')).map((node) => node.innerText.trim()).filter(Boolean).reverse();
      for (const nestedText of nestedTexts) {
        const index = rawText.lastIndexOf(nestedText);
        if (index >= 0) rawText = `${rawText.slice(0, index)}${rawText.slice(index + nestedText.length)}`.trim();
      }
      return {
        index,
        comment_id: replyMatch?.[1] || commentMatch?.[1] || "",
        parent_comment_id: replyMatch ? (commentMatch?.[1] || "") : "",
        author: (authorLink?.innerText || "").trim(),
        timestamp_label: dateLink?.getAttribute("aria-label") || dateLink?.getAttribute("title") || (dateLink?.innerText || "").trim(),
        permalink: href,
        raw_text: rawText,
        images: imagesFrom(comment),
      };
    });

    let postRawText = top.innerText.trim();
    for (const commentText of commentNodes.map((node) => node.innerText.trim()).filter(Boolean).reverse()) {
      const index = postRawText.lastIndexOf(commentText);
      if (index >= 0) postRawText = `${postRawText.slice(0, index)}${postRawText.slice(index + commentText.length)}`.trim();
    }
    const controls = Array.from(top.querySelectorAll('[role="button"],button'));
    const commentButton = controls.find((control) => (control.getAttribute("aria-label") || "").startsWith("コメントする"));
    const expectedMatch = (commentButton?.innerText || "").replaceAll(",", "").match(/[0-9]+/);
    const commentImageSources = comments.flatMap((comment) => comment.images.map((image) => image.src));
    const eventLinks = Array.from(top.querySelectorAll('a[href*="/events/"]')).map((link) => ({
      url: link.href,
      title: (link.getAttribute("aria-label") || link.innerText || "").trim(),
    })).filter((event, index, events) => event.url && events.findIndex((candidate) => candidate.url.split("?")[0] === event.url.split("?")[0]) === index);

    return {
      id: args.postId,
      url: args.url,
      fetched_at: new Date().toISOString(),
      expected_comment_count: Number(expectedMatch?.[0] || 0),
      post_raw_text: postRawText,
      post_images: imagesFrom(top).filter((image) => !commentImageSources.includes(image.src)),
      comments,
      event_links: eventLinks,
      control_labels: controls.map((control) => (control.getAttribute("aria-label") || control.innerText || "").trim()).filter(Boolean),
    };
  }, { groupId, postId: post.id, url: post.url, topArticleSelector });
}

async function capturePost(tab, post) {
  const failed = { id: post.id, url: post.url, status: "failed" };
  try {
    if ((await tab.url()) !== post.url) await tab.goto(post.url);
    await tab.playwright.domSnapshot();
    let top = tab.playwright.locator(topArticleSelector);
    let count = await top.count();
    if (count === 0) {
      await tab.playwright.waitForTimeout(1200);
      await tab.playwright.domSnapshot();
      top = tab.playwright.locator(topArticleSelector);
      count = await top.count();
    }
    if (count !== 1) throw new Error(`top-article-${count}`);

    for (let pass = 0; pass < 20; pass += 1) {
      const more = top.getByRole("button", { name: "もっと見る", exact: true });
      const moreCount = await more.count();
      if (moreCount === 0) break;
      await more.nth(0).click();
      await tab.playwright.domSnapshot();
      top = tab.playwright.locator(topArticleSelector);
    }

    let result = await extractPost(tab, post);
    if (!result) throw new Error("extract-null");
    const expected = result.expected_comment_count || 0;
    let lastCount = result.comments.length;
    let stablePasses = 0;
    for (let pass = 0; expected > lastCount && pass < 30; pass += 1) {
      await tab.cua.scroll({ x: 900, y: 1000, scrollY: 1521, scrollX: 0 });
      await tab.playwright.waitForTimeout(650);
      await tab.playwright.domSnapshot();
      const next = await extractPost(tab, post);
      if (!next) break;
      const nextCount = next.comments.length;
      stablePasses = nextCount === lastCount ? stablePasses + 1 : 0;
      result = next;
      lastCount = nextCount;
      if (stablePasses >= 3) break;
    }

    for (let pass = 0; pass < 40; pass += 1) {
      const replyLabel = result.control_labels.find((label) => /(?:[0-9]+件の返信.*(?:表示|見る)|返信を表示|返信を見る)/.test(label));
      if (!replyLabel) break;
      await tab.playwright.domSnapshot();
      top = tab.playwright.locator(topArticleSelector);
      const reply = top.getByRole("button", { name: replyLabel, exact: true });
      const replyCount = await reply.count();
      if (replyCount === 0) break;
      await reply.nth(0).click();
      await tab.playwright.domSnapshot();
      const next = await extractPost(tab, post);
      if (!next) break;
      result = next;
    }
    return { ...result, id: post.id, url: post.url, status: "recovered" };
  } catch (error) {
    return { ...failed, error: String(error?.message || error).slice(0, 500) };
  }
}

export function createFacebookGroupCrawler({ tabs, posts, checkpointPath }) {
  const checkpoint = JSON.parse(fs.readFileSync(checkpointPath, "utf8"));
  const completedIds = new Set(checkpoint.posts.map((post) => String(post.id)));

  function record(result) {
    if (result.status === "recovered") {
      const index = checkpoint.posts.findIndex((post) => String(post.id) === String(result.id));
      if (index >= 0) checkpoint.posts[index] = result;
      else checkpoint.posts.push(result);
      checkpoint.errors = checkpoint.errors.filter((error) => String(error.id) !== String(result.id));
      completedIds.add(String(result.id));
    } else {
      const index = checkpoint.errors.findIndex((error) => String(error.id) === String(result.id));
      const attempts = (index >= 0 ? checkpoint.errors[index].attempts || 1 : 0) + 1;
      const error = { ...result, attempts };
      if (index >= 0) checkpoint.errors[index] = error;
      else checkpoint.errors.push(error);
    }
    fs.writeFileSync(checkpointPath, JSON.stringify(checkpoint, null, 2));
  }

  function stats() {
    return {
      processed: completedIds.size,
      missing: posts.length - completedIds.size,
      errors: checkpoint.errors.length,
      comments: checkpoint.posts.reduce((sum, post) => sum + (post.comments?.length || 0), 0),
      commentPhotos: checkpoint.posts.reduce((sum, post) => sum + (post.comments || []).reduce((count, comment) => count + (comment.images?.length || 0), 0), 0),
    };
  }

  async function batch(total = 60) {
    const errorsById = new Map(checkpoint.errors.map((error) => [String(error.id), error]));
    const selected = posts.filter((post) => !completedIds.has(String(post.id)) && (errorsById.get(String(post.id))?.attempts || 0) < 3).slice(0, total);
    const lanes = tabs.map(() => []);
    selected.forEach((post, index) => lanes[index % tabs.length].push(post));
    const worker = async (tab, items) => {
      for (const post of items) record(await capturePost(tab, post));
    };
    await Promise.all(tabs.map((tab, index) => worker(tab, lanes[index])));
    return { ...stats(), selected: selected.length };
  }

  return { batch, stats };
}
