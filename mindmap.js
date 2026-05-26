(async function () {
  const BLUE = "#2B5797";
  const GREY = "#6D6E71";
  const LIGHT_BLUE = "#5B9BD5";
  const SUPPLIER_BG = "#E8F0FA";
  const SUPPLIERS_PER_ROW = 3;

  const container = d3.select("#mindmap");
  const width = window.innerWidth;
  const height = window.innerHeight;

  const response = await fetch("excipients.json");
  const routes = await response.json();

  const btnHeight = 18;
  const btnGapY = 4;
  const containerPadding = 8;
  const excipientGap = 20;
  const btnPaddingXMeasure = 8;
  const btnGapXMeasure = 5;
  const lineGapMeasure = 32;
  const categoryWhitespace = 120;
  const routeSpacing = 200;

  const trees = routes.map(r => d3.hierarchy(r, d => d.children));

  // Pre-measurement: global max category width across all trees
  const measureSvg = container.append("svg")
    .style("position", "absolute")
    .style("visibility", "hidden");

  let maxCategoryWidth = 0;

  trees.forEach(tree => {
    if (!tree.children) return;
    tree.children.forEach(category => {
      if (!category.children) return;
      category.children.forEach(excipient => {
        const excText = measureSvg.append("text")
          .style("font-size", "11px")
          .style("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
          .text(excipient.data.name);
        const excWidth = excText.node().getBBox().width + 28;
        excText.remove();

        const suppliers = excipient.data.suppliers || [];
        const rows = [];
        for (let i = 0; i < suppliers.length; i += SUPPLIERS_PER_ROW) {
          rows.push(suppliers.slice(i, i + SUPPLIERS_PER_ROW));
        }

        let maxRowWidth = 0;
        rows.forEach(row => {
          let rowW = 0;
          row.forEach(s => {
            const t = measureSvg.append("text")
              .style("font-size", "9px")
              .style("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
              .text(s.name);
            rowW += t.node().getBBox().width + btnPaddingXMeasure * 2 + btnGapXMeasure;
            t.remove();
          });
          rowW -= btnGapXMeasure;
          maxRowWidth = Math.max(maxRowWidth, rowW);
        });

        const supplierContainerWidth = maxRowWidth > 0 ? maxRowWidth + containerPadding * 2 : 0;
        const totalRowWidth = excWidth / 2 + lineGapMeasure + supplierContainerWidth + excWidth / 2;
        maxCategoryWidth = Math.max(maxCategoryWidth, totalRowWidth);
      });
    });
  });

  measureSvg.remove();

  const categorySpacing = maxCategoryWidth + categoryWhitespace;
  const maxCategoryCount = Math.max(...trees.map(t => t.children ? t.children.length : 0));
  const globalTreeWidth = maxCategoryCount * categorySpacing;

  // Position each tree vertically
  let globalY = 0;

  trees.forEach(tree => {
    const categoryCount = tree.children ? tree.children.length : 0;
    const treeWidth = categoryCount * categorySpacing;
    const offsetX = (globalTreeWidth - treeWidth) / 2;

    tree.x = globalTreeWidth / 2;
    tree.y = globalY;

    if (tree.children) {
      tree.children.forEach((category, i) => {
        category.x = offsetX + categorySpacing / 2 + i * categorySpacing;
        category.y = globalY + 100;
      });

      let maxBottom = globalY + 100;

      tree.children.forEach(category => {
        if (category.children) {
          const heights = category.children.map(excipient => {
            const supplierCount = excipient.data.suppliers ? excipient.data.suppliers.length : 0;
            const supplierRows = Math.max(1, Math.ceil(supplierCount / SUPPLIERS_PER_ROW));
            return Math.max(30, supplierRows * (btnHeight + btnGapY) - btnGapY + containerPadding * 2);
          });

          let yOffset = category.y + 80 + heights[0] / 2;
          category.children.forEach((excipient, i) => {
            excipient.x = category.x;
            excipient.y = yOffset;
            if (i < category.children.length - 1) {
              yOffset += heights[i] / 2 + excipientGap + heights[i + 1] / 2;
            } else {
              yOffset += heights[i] / 2;
            }
          });

          maxBottom = Math.max(maxBottom, yOffset);
        }
      });

      globalY = maxBottom + routeSpacing;
    } else {
      globalY += 200 + routeSpacing;
    }
  });

  // Create SVG
  const svg = container.append("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g");

  const zoom = d3.zoom()
    .scaleExtent([0.02, 2])
    .filter(function (event) {
      let el = event.target;
      while (el && el !== this) {
        if (el.tagName === "a") return false;
        el = el.parentNode;
      }
      return !event.button && (!event.ctrlKey || event.type === "wheel");
    })
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg.call(zoom);

  // Logo above first tree
  const logoW = 1200;
  const logoH = 240;
  const firstTreeY = trees[0].y;
  g.append("image")
    .attr("href", "pe-logo.png")
    .attr("x", globalTreeWidth / 2 - logoW / 2)
    .attr("y", firstTreeY - 380 - 200 - 440)
    .attr("width", logoW)
    .attr("height", logoH);

  // Hero title
  g.append("text")
    .attr("x", globalTreeWidth / 2)
    .attr("y", firstTreeY - 380)
    .attr("text-anchor", "middle")
    .style("font-size", "200px")
    .style("font-weight", "300")
    .style("font-style", "italic")
    .style("fill", BLUE)
    .style("opacity", 0.7)
    .style("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
    .text("The Pharmaceutical Excipients Landscape 2026");

  // Render all trees
  trees.forEach(tree => {
    const allNodes = tree.descendants();
    const allLinks = tree.links();

    // Connection paths
    g.selectAll(null)
      .data(allLinks)
      .join("path")
      .attr("d", d => {
        return `M${d.source.x},${d.source.y}
                C${d.source.x},${(d.source.y + d.target.y) / 2}
                 ${d.target.x},${(d.source.y + d.target.y) / 2}
                 ${d.target.x},${d.target.y}`;
      })
      .attr("fill", "none")
      .attr("stroke", d => d.source.depth === 0 ? GREY : "#cccccc")
      .attr("stroke-width", d => d.source.depth === 0 ? 2 : 1.2)
      .attr("stroke-opacity", d => d.source.depth === 0 ? 0.4 : 0.6);

    // Nodes
    const nodeGroups = g.selectAll(null)
      .data(allNodes)
      .join("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${d.x},${d.y})`);

    nodeGroups.each(function (d) {
      const node = d3.select(this);
      const text = node.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .style("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
        .text(d.data.name);

      if (d.depth === 0) {
        text.style("font-size", "16px").style("font-weight", "bold").style("fill", "#ffffff");
      } else if (d.depth === 1) {
        text.style("font-size", "12px").style("font-weight", "bold").style("fill", "#ffffff");
      } else {
        text.style("font-size", "11px").style("font-weight", "normal").style("fill", "#333333");
      }

      const bbox = text.node().getBBox();
      const paddingX = d.depth === 0 ? 24 : d.depth === 1 ? 16 : 14;
      const paddingY = d.depth === 0 ? 12 : d.depth === 1 ? 10 : 8;
      const rectWidth = bbox.width + paddingX * 2;
      const rectHeight = bbox.height + paddingY * 2;
      const borderRadius = d.depth >= 2 ? rectHeight / 2 : 8;

      node.insert("rect", "text")
        .attr("x", -rectWidth / 2)
        .attr("y", -rectHeight / 2)
        .attr("width", rectWidth)
        .attr("height", rectHeight)
        .attr("rx", borderRadius)
        .attr("ry", borderRadius)
        .attr("fill", d.depth === 0 ? GREY : d.depth === 1 ? BLUE : "#ffffff")
        .attr("stroke", d.depth >= 2 ? BLUE : "none")
        .attr("stroke-width", d.depth >= 2 ? 1.5 : 0);

      // Supplier buttons
      if (d.depth === 2 && d.data.suppliers && d.data.suppliers.length > 0) {
        const suppliers = d.data.suppliers;
        const lineGap = 20;
        const containerX = rectWidth / 2 + lineGap + 12;

        const supplierGroup = node.append("g")
          .attr("class", "supplier-group")
          .attr("transform", `translate(${containerX}, 0)`);

        const btnPaddingX = 8;
        const btnGapX = 5;

        const measured = suppliers.map(s => {
          const t = supplierGroup.append("text")
            .style("font-size", "9px")
            .style("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
            .text(s.name);
          const b = t.node().getBBox();
          t.remove();
          return { supplier: s, textWidth: b.width };
        });

        const rows = [];
        for (let i = 0; i < measured.length; i += SUPPLIERS_PER_ROW) {
          rows.push(measured.slice(i, i + SUPPLIERS_PER_ROW));
        }

        let maxRowWidth = 0;
        rows.forEach(row => {
          let rowW = 0;
          row.forEach(m => { rowW += m.textWidth + btnPaddingX * 2 + btnGapX; });
          rowW -= btnGapX;
          maxRowWidth = Math.max(maxRowWidth, rowW);
        });

        const containerWidth = maxRowWidth + containerPadding * 2;
        const containerHeight = rows.length * (btnHeight + btnGapY) - btnGapY + containerPadding * 2;

        node.insert("line", ".supplier-group")
          .attr("x1", rectWidth / 2)
          .attr("y1", 0)
          .attr("x2", containerX)
          .attr("y2", 0)
          .attr("stroke", "#cccccc")
          .attr("stroke-width", 1.2)
          .attr("stroke-opacity", 0.6);

        supplierGroup.append("rect")
          .attr("x", 0)
          .attr("y", -containerHeight / 2)
          .attr("width", containerWidth)
          .attr("height", containerHeight)
          .attr("rx", 6)
          .attr("ry", 6)
          .attr("fill", SUPPLIER_BG)
          .attr("stroke", "#d0dcea")
          .attr("stroke-width", 1);

        rows.forEach((row, rowIndex) => {
          let xPos = containerPadding;
          const yPos = -containerHeight / 2 + containerPadding + rowIndex * (btnHeight + btnGapY) + btnHeight / 2;

          row.forEach(m => {
            const btnW = m.textWidth + btnPaddingX * 2;
            const wrapper = m.supplier.link
              ? supplierGroup.append("a").attr("href", m.supplier.link).attr("target", "_blank")
              : supplierGroup.append("g");

            const btnGroup = wrapper
              .attr("transform", `translate(${xPos}, ${yPos})`)
              .style("cursor", m.supplier.link ? "pointer" : "default");

            btnGroup.append("rect")
              .attr("x", 0)
              .attr("y", -btnHeight / 2)
              .attr("width", btnW)
              .attr("height", btnHeight)
              .attr("rx", btnHeight / 2)
              .attr("ry", btnHeight / 2)
              .attr("fill", LIGHT_BLUE)
              .attr("opacity", 0.85);

            btnGroup.append("text")
              .attr("x", btnPaddingX)
              .attr("y", 0)
              .attr("dy", "0.35em")
              .style("font-size", "9px")
              .style("font-weight", "500")
              .style("fill", "#ffffff")
              .style("font-family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
              .text(m.supplier.name);

            if (m.supplier.link) {
              btnGroup
                .on("mouseenter", function () {
                  d3.select(this).select("rect")
                    .transition().duration(100)
                    .attr("opacity", 1)
                    .style("filter", "drop-shadow(0 1px 3px rgba(43,87,151,0.3))");
                })
                .on("mouseleave", function () {
                  d3.select(this).select("rect")
                    .transition().duration(100)
                    .attr("opacity", 0.85)
                    .style("filter", "none");
                });
            }

            xPos += btnW + btnGapX;
          });
        });
      }
    });

    // Hover for route and category nodes
    nodeGroups
      .style("cursor", "default")
      .on("mouseenter", function (event, d) {
        if (d.depth < 2) {
          d3.select(this).select("rect")
            .transition().duration(150)
            .style("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.25))");
        }
      })
      .on("mouseleave", function (event, d) {
        if (d.depth < 2) {
          d3.select(this).select("rect")
            .transition().duration(150)
            .style("filter", "none");
        }
      });
  });

  // Initial viewport: show first route with its categories
  const firstTree = trees[0];
  let minX = firstTree.x, maxX = firstTree.x;
  let minY = firstTree.y, maxY = firstTree.y;

  if (firstTree.children) {
    firstTree.children.forEach(c => {
      minX = Math.min(minX, c.x);
      maxX = Math.max(maxX, c.x);
      maxY = Math.max(maxY, c.y);
    });
  }

  const padding = 150;
  minX -= padding;
  maxX += padding;
  minY -= padding;
  maxY += padding;

  const boundsWidth = maxX - minX;
  const boundsHeight = maxY - minY;
  const scale = Math.min(width / boundsWidth, height / boundsHeight, 1);
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  const initialTransform = d3.zoomIdentity
    .translate(width / 2, height / 2)
    .scale(scale)
    .translate(-centerX, -centerY);

  svg.call(zoom.transform, initialTransform);
})();
